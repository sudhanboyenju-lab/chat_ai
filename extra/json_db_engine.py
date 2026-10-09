import json


def load_services():
    with open("services_db.json", "r", encoding="utf-8") as f:
        return json.load(f)

def search_services(query, services):
    """Simple keyword search across service names."""
    query_lower = query.lower()
    matches = []

    for service_id, service_data in services.items():
        if query_lower in service_id.lower() or query_lower in service_data["name"].lower():
            matches.append(service_data)

    return matches

def get_service(service_id, services):
    """Direct exact lookup by ID."""
    return services.get(service_id)