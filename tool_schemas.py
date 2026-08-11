from typing import Optional
from pydantic import BaseModel, Field
from maximo_mcp_server import (
    fetch_service_requests,
    fetch_locations,
    fetch_classifications,
)


class ServiceRequestArgs(BaseModel):
    ticket_id: Optional[str] = Field(
        default=None,
        description="Specific ticket identifier or comma-separated list of IDs.",
    )
    location_id: Optional[str] = Field(
        default=None,
        description="Location code or comma-separated list of locations.",
    )
    asset_num: Optional[str] = Field(default=None, description="Asset identifier code.")
    status: Optional[str] = Field(
        default=None,
        description="Ticket status ('NEW', 'QUEUED', 'PENDING', 'INPROG', 'RESOLVED', 'CLOSED').",
    )
    reported_by: Optional[str] = Field(
        default=None, description="Person ID who reported the issue."
    )
    owner: Optional[str] = Field(
        default=None, description="Owner or owner group assigned to the ticket."
    )
    query: Optional[str] = Field(
        default=None, description="Text query searching across ticket description."
    )
    saved_query: Optional[str] = Field(
        default=None,
        description=(
            "Maximo saved query ('SERVICEREQUEST', 'SERVICEREQUESTHISTORY', "
            "'VIEWSR:MY S.S. SR\\'S', 'SR:All Service Requests')."
        ),
    )
    count_only: bool = Field(
        default=False,
        description="Set True to return total record count via ?count=1 parameter.",
    )
    limit: int = Field(default=10, description="Maximum number of records to return.")


class LocationArgs(BaseModel):
    location_id: Optional[str] = Field(
        default=None, description="Location identifier code (e.g. 'LOC-102')."
    )
    site_id: Optional[str] = Field(
        default=None, description="Site identifier filter (e.g. 'BEDFORD')."
    )
    query: Optional[str] = Field(
        default=None, description="Location code or description search query."
    )
    status: Optional[str] = Field(
        default=None,
        description="Location status (e.g. 'OPERATIONAL', 'DECOMMISSIONED').",
    )
    location_type: Optional[str] = Field(
        default=None, description="Location type filter (e.g. 'OPERATOR', 'COURIER')."
    )
    parent_id: Optional[str] = Field(
        default=None, description="Parent location code for hierarchical drill-down."
    )
    saved_query: Optional[str] = Field(
        default=None,
        description="Maximo saved query ('SERVICEREQUESTLOCATION' or 'SERVICEREQUESTROOTLOCATION').",
    )
    count_only: bool = Field(
        default=False,
        description="Set True to return total record count via ?count=1 parameter.",
    )
    limit: int = Field(default=10, description="Maximum number of records to return.")


class ClassificationArgs(BaseModel):
    classification_id: Optional[str] = Field(
        default=None, description="Classification ID filter (e.g. 'WORKORDER', 'HVAC')."
    )
    query: Optional[str] = Field(
        default=None,
        description="Text query matching classification ID or description.",
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent class structure identifier for hierarchical drill-down.",
    )
    show_in_sr: Optional[bool] = Field(
        default=None,
        description="True to filter to classifications available for Service Requests.",
    )
    saved_query: Optional[str] = Field(
        default=None,
        description="Maximo saved query ('CLASSIFICATIONLOOKUP' or 'TASKCLASSIFICATIONLOOKUP').",
    )
    count_only: bool = Field(
        default=False,
        description="Set True to return total record count via ?count=1 parameter.",
    )
    limit: int = Field(default=10, description="Maximum number of records to return.")


TOOL_FUNCTIONS = {
    "fetch_service_requests": fetch_service_requests,
    "fetch_locations": fetch_locations,
    "fetch_classifications": fetch_classifications,
}
TOOL_ARG_MODELS = {
    "fetch_service_requests": ServiceRequestArgs,
    "fetch_locations": LocationArgs,
    "fetch_classifications": ClassificationArgs,
}

TOOL_SCHEMAS = []
for name, func in TOOL_FUNCTIONS.items():
    doc_desc = func.__doc__.split("Args:")[0].strip() if func.__doc__ else ""
    arg_model = TOOL_ARG_MODELS[name]

    TOOL_SCHEMAS.append(
        {
            "type": "function",
            "function": {
                "name": name,
                "description": doc_desc,
                "parameters": arg_model.model_json_schema(),
            },
        }
    )
