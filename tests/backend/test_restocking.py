"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking candidates and submitted restocking orders."""

    def test_get_restocking_candidates(self, client):
        """Test getting restocking candidates."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        for field in ["sku", "name", "category", "warehouse", "quantity_on_hand",
                      "forecasted_demand", "shortfall", "unit_cost", "line_cost",
                      "lead_time_days"]:
            assert field in first

    def test_restocking_candidates_shortfall_and_cost(self, client):
        """Test that shortfall is positive and line cost matches shortfall times unit cost."""
        data = client.get("/api/restocking/candidates").json()

        for candidate in data:
            assert candidate["shortfall"] > 0
            assert candidate["shortfall"] == candidate["forecasted_demand"] - candidate["quantity_on_hand"]
            assert abs(candidate["line_cost"] - candidate["shortfall"] * candidate["unit_cost"]) < 0.01
            assert candidate["lead_time_days"] > 0

    def test_restocking_candidates_priority_order(self, client):
        """Test that candidates are sorted by shortfall, largest first."""
        data = client.get("/api/restocking/candidates").json()

        shortfalls = [c["shortfall"] for c in data]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_restocking_candidates_only_forecast_items(self, client):
        """Test that every candidate has a demand forecast."""
        candidates = client.get("/api/restocking/candidates").json()
        forecast_skus = {f["item_sku"] for f in client.get("/api/demand").json()}

        for candidate in candidates:
            assert candidate["sku"] in forecast_skus

    def test_create_restocking_order(self, client):
        """Test submitting an order and that it is priced from server data."""
        candidates = client.get("/api/restocking/candidates").json()
        chosen = candidates[:2]
        assert len(chosen) == 2

        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": c["sku"], "quantity": c["shortfall"]} for c in chosen]
        })
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == 2
        assert abs(order["total_value"] - sum(c["line_cost"] for c in chosen)) < 0.01
        # Order lead time is that of its slowest item
        assert order["lead_time_days"] == max(c["lead_time_days"] for c in chosen)

    def test_create_restocking_order_ignores_client_prices(self, client):
        """Test that client-supplied prices cannot change the order total."""
        candidate = client.get("/api/restocking/candidates").json()[0]

        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": 1, "unit_cost": 0.01}]
        })
        assert response.status_code == 201
        assert abs(response.json()["total_value"] - candidate["unit_cost"]) < 0.01

    def test_create_restocking_order_unknown_sku(self, client):
        """Test submitting a SKU that is not a restocking candidate."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 1}]
        })
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_restocking_order_quantity_over_shortfall(self, client):
        """Test that ordering more than the shortfall is rejected."""
        candidate = client.get("/api/restocking/candidates").json()[0]

        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": candidate["shortfall"] + 1}]
        })
        assert response.status_code == 400

    def test_create_restocking_order_invalid_quantity(self, client):
        """Test that a zero quantity is rejected."""
        candidate = client.get("/api/restocking/candidates").json()[0]

        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": 0}]
        })
        assert response.status_code == 400

    def test_create_restocking_order_empty_and_duplicate(self, client):
        """Test that empty orders and duplicate SKUs are rejected."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

        candidate = client.get("/api/restocking/candidates").json()[0]
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": 1}] * 2
        })
        assert response.status_code == 400

    def test_create_restocking_order_over_budget(self, client):
        """Test that an order exceeding the stated budget is rejected."""
        candidate = client.get("/api/restocking/candidates").json()[0]

        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": candidate["shortfall"]}],
            "budget": 1
        })
        assert response.status_code == 400

    def test_get_restocking_orders_includes_created_order(self, client):
        """Test that a submitted order appears in the orders list."""
        candidate = client.get("/api/restocking/candidates").json()[0]
        created = client.post("/api/restocking/orders", json={
            "items": [{"sku": candidate["sku"], "quantity": 1}]
        }).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        # Orders persist across tests, so look the order up by id rather than counting
        orders = response.json()
        assert any(o["id"] == created["id"] for o in orders)
        assert orders[0]["id"] == created["id"]
