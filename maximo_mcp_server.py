import sys
from typing import Optional, Dict, Any
from mcp.server.mcpserver import MCPServer
from maximo_client import get_service_requests, get_locations, get_classifications

# Initialize the Maximo MCP Server
mcp = MCPServer(
    name="maximo-mcp-server",
    version="1.0.0"
)

@mcp.tool()
def fetch_service_requests(
    ticket_id: Optional[str] = None,
    location_id: Optional[str] = None,
    asset_num: Optional[str] = None,
    status: Optional[str] = None,
    reported_by: Optional[str] = None,
    owner: Optional[str] = None,
    query: Optional[str] = None,
    saved_query: Optional[str] = None,
    count_only: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch, search, or count Maximo Service Requests / Tickets (MXAPISR).
    Use this tool whenever asked to list, search, or count the total number of service requests/tickets.
    Pass count_only=True to instantly fetch total count via Maximo ?count=1 OSLC parameter.

    Args:
        ticket_id: Optional specific ticket identifier or comma-separated list of IDs.
        location_id: Optional location code or comma-separated list of locations.
        asset_num: Optional asset identifier code.
        status: Optional ticket status ('NEW', 'QUEUED', 'PENDING', 'INPROG', 'RESOLVED', 'CLOSED').
        reported_by: Optional person ID who reported the issue.
        owner: Optional owner or owner group assigned to ticket.
        query: Optional text query searching across ticket description.
        saved_query: Optional Maximo saved query ('SERVICEREQUEST', 'SERVICEREQUESTHISTORY', 'VIEWSR:MY S.S. SR\'S', 'SR:All Service Requests').
        count_only: Set True to return total record count via ?count=1 parameter.
        limit: Maximum number of records to return (default: 10).
    """
    return get_service_requests(
        ticket_id=ticket_id,
        location_id=location_id,
        asset_num=asset_num,
        status=status,
        reported_by=reported_by,
        owner=owner,
        query=query,
        saved_query=saved_query,
        count_only=count_only,
        limit=limit
    )



@mcp.tool()
def fetch_locations(
    location_id: Optional[str] = None,
    site_id: Optional[str] = None,
    query: Optional[str] = None,
    status: Optional[str] = None,
    location_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    saved_query: Optional[str] = None,
    count_only: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch, search, or count Maximo Locations (MXAPILOCATION).
    Pass count_only=True to instantly fetch total count via Maximo ?count=1 OSLC parameter.

    Args:
        location_id: Optional location identifier code (e.g. 'LOC-102').
        site_id: Optional site identifier filter (e.g. 'BEDFORD').
        query: Optional location code or description search query.
        status: Optional location status (e.g. 'OPERATIONAL', 'DECOMMISSIONED').
        location_type: Optional location type filter (e.g. 'OPERATOR', 'COURIER').
        parent_id: Optional parent location code for hierarchical drill-down.
        saved_query: Optional Maximo saved query ('SERVICEREQUESTLOCATION' or 'SERVICEREQUESTROOTLOCATION').
        count_only: Set True to return total record count via ?count=1 parameter.
        limit: Maximum number of records to return (default: 10).
    """
    return get_locations(
        location_id=location_id,
        site_id=site_id,
        query=query,
        status=status,
        location_type=location_type,
        parent_id=parent_id,
        saved_query=saved_query,
        count_only=count_only,
        limit=limit
    )



@mcp.tool()
def fetch_classifications(
    classification_id: Optional[str] = None,
    query: Optional[str] = None,
    parent_id: Optional[str] = None,
    show_in_sr: Optional[bool] = None,
    saved_query: Optional[str] = None,
    count_only: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch, search, or count Maximo Class Structure / Classifications (MXAPICLASSSTRUCTURE).
    Pass count_only=True to instantly fetch total count via Maximo ?count=1 OSLC parameter.

    Args:
        classification_id: Optional classification ID filter (e.g. 'WORKORDER', 'HVAC').
        query: Optional text query matching classification ID or description.
        parent_id: Optional parent class structure identifier for hierarchical drill-down.
        show_in_sr: Optional boolean filter (true = show classifications available for Service Requests).
        saved_query: Optional Maximo saved query ('CLASSIFICATIONLOOKUP' or 'TASKCLASSIFICATIONLOOKUP').
        count_only: Set True to return total record count via ?count=1 parameter.
        limit: Maximum number of records to return (default: 10).
    """
    return get_classifications(
        classification_id=classification_id,
        query=query,
        parent_id=parent_id,
        show_in_sr=show_in_sr,
        saved_query=saved_query,
        count_only=count_only,
        limit=limit
    )



if __name__ == "__main__":
    print("Starting Maximo MCP Server on stdio...", file=sys.stderr)
    mcp.run()
