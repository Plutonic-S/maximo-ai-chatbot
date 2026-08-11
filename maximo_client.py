import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MAXIMO_BASE_URL = os.getenv("MAXIMO_BASE_URL", "https://REDACTED-HOST.example.net/maximo")
MAXIMO_API_KEY = os.getenv("MAXIMO_API_KEY")

def _get_headers() -> Dict[str, str]:
    """Helper to return Maximo API request headers."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    if MAXIMO_API_KEY:
        headers["apikey"] = MAXIMO_API_KEY
    return headers


def _clean_oslc_member(item: Dict[str, Any]) -> Dict[str, Any]:
    """Strip 'spi:' prefixes and internal OSLC metadata keys from item dictionary."""
    cleaned = {}
    for k, v in item.items():
        if k.startswith("_") or k.endswith("_collectionref") or k.startswith("rdf:"):
            continue
        key_name = k.replace("spi:", "")
        cleaned[key_name] = v
    return cleaned


def _deduplicate_items(items: List[Dict[str, Any]], unique_key: str) -> List[Dict[str, Any]]:
    """Deduplicate member items based on a specific unique property key (e.g., 'location', 'ticketid')."""
    seen = set()
    deduped = []
    for item in items:
        val = item.get(unique_key)
        if val and val in seen:
            continue
        if val:
            seen.add(val)
        deduped.append(item)
    return deduped


def _format_in_clause(field: str, val_str: str) -> str:
    """Format string value (e.g. 'AIR101, 764750' or 'AIR101 and 764750') into valid OSLC query clause."""
    import re
    items = [x.strip() for x in re.split(r'[,|]|\band\b|\bor\b', val_str) if x.strip()]
    if len(items) > 1:
        quoted = ",".join([f'"{x}"' for x in items])
        return f'{field} in [{quoted}]'
    elif len(items) == 1:
        return f'{field}="{items[0]}"'
    return f'{field}="{val_str}"'


def get_service_requests(
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
    Fetch Maximo Service Requests / Tickets (MXAPISR).

    Args:
        ticket_id: Optional specific ticket identifier or multiple comma-separated IDs (e.g. '1001' or '1001, 1002').
        location_id: Optional location code or multiple locations (e.g. 'LOC-102' or 'AIR101, 764750').
        asset_num: Optional asset identifier code (e.g. 'PUMP-01').
        status: Optional ticket status (e.g. 'NEW', 'QUEUED', 'PENDING', 'INPROG', 'RESOLVED', 'CLOSED').
        reported_by: Optional person ID who reported the issue.
        owner: Optional owner or owner group assigned to ticket.
        query: Optional text query searching across ticket description or long description.
        saved_query: Optional Maximo saved query ('SERVICEREQUEST', 'SERVICEREQUESTHISTORY', 'VIEWSR:MY S.S. SR\'S', 'SR:All Service Requests').
        count_only: If True, uses ?count=1 parameter to return total count of matching records.
        limit: Maximum number of records to return (default: 10).

    Returns:
        Dict containing matching service requests, total count, or error details.
    """
    url = f"{MAXIMO_BASE_URL.rstrip('/')}/api/os/MXAPISR"
    
    where_clauses = []
    if ticket_id:
        where_clauses.append(_format_in_clause("ticketid", ticket_id))
    if location_id:
        where_clauses.append(_format_in_clause("location", location_id))
    if asset_num:
        where_clauses.append(_format_in_clause("assetnum", asset_num))
    if status:
        where_clauses.append(_format_in_clause("status", status))
    if reported_by:
        where_clauses.append(f'reportedby="{reported_by}"')
    if owner:
        where_clauses.append(f'owner="{owner}" or ownergroup="{owner}"')
    if query:
        where_clauses.append(f'description="%{query}%"')
        
    params = {
        "oslc.select": "ticketid,description,description_longdescription,location,assetnum,status,reportedby,affectedperson,owner,ownergroup,reportedpriority,internalpriority,reportdate,targetstart,targetfinish,siteid,orgid"
    }

    if count_only:
        params["count"] = "1"
    else:
        # Fetch extra to account for deduplication; pageSize is meaningless (and Maximo
        # rejects pageSize=0) when count_only skips fetching rows entirely.
        params["oslc.pageSize"] = str(max(limit, 1) * 2)

    if saved_query:
        params["savedQuery"] = saved_query

    if where_clauses:
        params["oslc.where"] = " and ".join(where_clauses)

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if count_only or "totalCount" in data:
            total_cnt = data.get("totalCount", 0)
            return {
                "success": True,
                "total_count": total_cnt,
                "count": total_cnt,
                "message": f"Total count of service requests in Maximo is {total_cnt}",
                "service_requests": []
            }

        raw_members = data.get("member", data.get("rdfs:member", []))
        cleaned_members = [_clean_oslc_member(m) for m in raw_members]
        deduped_members = _deduplicate_items(cleaned_members, "ticketid")[:limit]

        return {
            "success": True,
            "count": len(deduped_members),
            "service_requests": deduped_members
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch service requests from Maximo: {str(e)}",
            "service_requests": []
        }


def get_locations(
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
    Fetch Maximo Locations (MXAPILOCATION).

    Args:
        location_id: Optional location identifier code (e.g. 'LOC-102').
        site_id: Optional site identifier filter (e.g. 'BEDFORD').
        query: Optional location code or description search query.
        status: Optional location status (e.g. 'OPERATIONAL', 'DECOMMISSIONED').
        location_type: Optional location type filter (e.g. 'OPERATOR', 'COURIER').
        parent_id: Optional parent location code for hierarchical drill-down.
        saved_query: Optional Maximo saved query ('SERVICEREQUESTLOCATION' or 'SERVICEREQUESTROOTLOCATION').
        count_only: If True, uses ?count=1 parameter to return total count of matching records.
        limit: Maximum number of records to return (default: 10).

    Returns:
        Dict containing location details, total count, or error details.
    """
    url = f"{MAXIMO_BASE_URL.rstrip('/')}/api/os/MXAPILOCATION"
    
    where_clauses = []
    if location_id:
        where_clauses.append(f'location="%{location_id}%"')
    if site_id:
        where_clauses.append(f'siteid="{site_id}"')
    if query:
        where_clauses.append(f'location="%{query}%" or description="%{query}%"')
    if status:
        where_clauses.append(f'status="{status}"')
    if location_type:
        where_clauses.append(f'type="{location_type}"')
    if parent_id:
        where_clauses.append(f'parent="{parent_id}"')

    params = {
        "oslc.select": "location,description,siteid,orgid,status,type,parent,hierarchypath,showinworkcenter"
    }

    if count_only:
        params["count"] = "1"
    else:
        # Fetch extra to account for deduplication across hierarchies; pageSize is meaningless
        # (and Maximo rejects pageSize=0) when count_only skips fetching rows entirely.
        params["oslc.pageSize"] = str(max(limit, 1) * 2)

    if saved_query:
        params["savedQuery"] = saved_query

    if where_clauses:
        params["oslc.where"] = " and ".join(where_clauses)

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if count_only or "totalCount" in data:
            total_cnt = data.get("totalCount", 0)
            return {
                "success": True,
                "total_count": total_cnt,
                "count": total_cnt,
                "message": f"Total count of locations in Maximo is {total_cnt}",
                "locations": []
            }

        raw_members = data.get("member", data.get("rdfs:member", []))
        cleaned_members = [_clean_oslc_member(m) for m in raw_members]
        deduped_members = _deduplicate_items(cleaned_members, "location")[:limit]

        return {
            "success": True,
            "count": len(deduped_members),
            "locations": deduped_members
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch locations from Maximo: {str(e)}",
            "locations": []
        }


def get_classifications(
    classification_id: Optional[str] = None,
    query: Optional[str] = None,
    parent_id: Optional[str] = None,
    show_in_sr: Optional[bool] = None,
    saved_query: Optional[str] = None,
    count_only: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch Maximo Class Structure / Classifications (MXAPICLASSSTRUCTURE).

    Args:
        classification_id: Optional classification ID filter (e.g. 'WORKORDER', 'HVAC').
        query: Optional text query matching classification ID or description.
        parent_id: Optional parent class structure identifier for hierarchical drill-down.
        show_in_sr: Optional boolean filter (true = show classifications available for Service Requests).
        saved_query: Optional Maximo saved query ('CLASSIFICATIONLOOKUP' or 'TASKCLASSIFICATIONLOOKUP').
        count_only: If True, uses ?count=1 parameter to return total count of matching records.
        limit: Maximum number of records to return (default: 10).

    Returns:
        Dict containing classification records, total count, or error details.
    """
    url = f"{MAXIMO_BASE_URL.rstrip('/')}/api/os/MXAPICLASSSTRUCTURE"
    
    where_clauses = []
    if classification_id:
        where_clauses.append(f'classificationid="%{classification_id}%"')
    if query:
        where_clauses.append(f'classificationid="%{query}%" or description="%{query}%"')
    if parent_id:
        where_clauses.append(f'parent="{parent_id}"')
    if show_in_sr is not None:
        where_clauses.append(f'show={"true" if show_in_sr else "false"}')

    params = {
        "oslc.select": "classstructureid,classificationid,description,parent,hierarchypath,show,type,siteid,orgid"
    }

    if count_only:
        params["count"] = "1"
    else:
        # pageSize is meaningless (and Maximo rejects pageSize=0) when count_only skips
        # fetching rows entirely.
        params["oslc.pageSize"] = str(max(limit, 1) * 2)

    if saved_query:
        params["savedQuery"] = saved_query

    if where_clauses:
        params["oslc.where"] = " and ".join(where_clauses)

    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if count_only or "totalCount" in data:
            total_cnt = data.get("totalCount", 0)
            return {
                "success": True,
                "total_count": total_cnt,
                "count": total_cnt,
                "message": f"Total count of classifications in Maximo is {total_cnt}",
                "classifications": []
            }

        raw_members = data.get("member", data.get("rdfs:member", []))
        cleaned_members = [_clean_oslc_member(m) for m in raw_members]
        deduped_members = _deduplicate_items(cleaned_members, "classificationid")[:limit]

        return {
            "success": True,
            "count": len(deduped_members),
            "classifications": deduped_members
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch classifications from Maximo: {str(e)}",
            "classifications": []
        }


