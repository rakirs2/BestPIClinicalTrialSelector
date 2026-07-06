"""Transform raw ClinicalTrials.gov payloads into normalized dataclasses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .models import (
    ArmGroupRecord,
    ConditionRecord,
    ContactRecord,
    EligibilityRecord,
    InterventionRecord,
    InvestigatorRecord,
    KeywordRecord,
    LocationRecord,
    MeshTermRecord,
    NormalizedStudy,
    OutcomeRecord,
    ResultEventRecord,
    SponsorRecord,
    StudyRecord,
)


def normalize_full_study(raw: Dict[str, Any]) -> NormalizedStudy:
    """Extract structured records for a single study payload."""

    protocol = raw.get("protocolSection", {}) or {}
    derived = raw.get("derivedSection", {}) or {}
    status_module = protocol.get("statusModule", {}) or {}
    identification_module = protocol.get("identificationModule", {}) or {}
    design_module = protocol.get("designModule", {}) or {}
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {}) or {}
    description_module = protocol.get("descriptionModule", {}) or {}
    conditions_module = protocol.get("conditionsModule", {}) or {}
    arms_module = protocol.get("armsInterventionsModule", {}) or {}
    outcomes_module = protocol.get("outcomesModule", {}) or {}
    eligibility_module = protocol.get("eligibilityModule", {}) or {}
    contacts_module = protocol.get("contactsLocationsModule", {}) or {}
    biospecimens_module = protocol.get("biospecimensModule", {}) or {}

    nct_id: str = identification_module.get("nctId") or identification_module.get("nctID")
    if not nct_id:
        raise ValueError("Study payload missing nctId")

    study_record = StudyRecord(
        nct_id=nct_id,
        brief_title=identification_module.get("briefTitle"),
        official_title=identification_module.get("officialTitle"),
        study_type=design_module.get("studyType"),
        phase=_first(design_module.get("phases")),
        enrollment=_safe_int(_get(design_module, "enrollmentInfo", "count")),
        enrollment_type=_get(design_module, "enrollmentInfo", "type"),
        overall_status=status_module.get("overallStatus"),
        start_date=_date_from_struct(status_module.get("startDateStruct")),
        completion_date=_date_from_struct(status_module.get("completionDateStruct")),
        primary_completion_date=_date_from_struct(status_module.get("primaryCompletionDateStruct")),
        last_update_post_date=_date_from_struct(status_module.get("lastUpdatePostDateStruct")),
        last_changed_date=status_module.get("lastUpdateSubmitDate"),
        study_first_post_date=_date_from_struct(status_module.get("studyFirstPostDateStruct")),
        results_first_post_date=_date_from_struct(status_module.get("resultsFirstPostDateStruct")),
        verification_date=status_module.get("statusVerifiedDate"),
        study_model=_get(design_module, "designInfo", "observationalModel"),
        masking=_get(design_module, "designInfo", "maskingInfo", "masking"),
        allocation=_get(design_module, "designInfo", "allocation"),
        intervention_model=_get(design_module, "designInfo", "interventionModel"),
        responsible_party=_format_responsible_party(sponsor_module.get("responsibleParty")),
        conditions_description=description_module.get("briefSummary") or description_module.get("detailedDescription"),
        design_primary_purpose=_get(design_module, "designInfo", "primaryPurpose"),
        biospec_retention=biospecimens_module.get("retention"),
        biospec_descr=biospecimens_module.get("description"),
        last_refreshed_on=datetime.now(timezone.utc),
    )

    sponsors = _sponsor_records(nct_id, sponsor_module)
    conditions = [ConditionRecord(nct_id=nct_id, name=name) for name in conditions_module.get("conditions", []) or []]
    keywords = [KeywordRecord(nct_id=nct_id, keyword=kw) for kw in conditions_module.get("keywords", []) or []]
    mesh_terms = _mesh_records(nct_id, derived)
    interventions = _interventions(nct_id, arms_module)
    arm_groups = _arm_groups(nct_id, arms_module)
    locations = _locations(nct_id, contacts_module)
    investigators = _investigators(nct_id, contacts_module)
    outcomes = _outcomes(nct_id, outcomes_module)
    eligibility = _eligibility(nct_id, eligibility_module)
    contacts = _contacts(nct_id, contacts_module)
    results = _result_events(nct_id, raw)

    return NormalizedStudy(
        study=study_record,
        sponsors=sponsors,
        conditions=conditions,
        keywords=keywords,
        mesh_terms=mesh_terms,
        interventions=interventions,
        arm_groups=arm_groups,
        locations=locations,
        investigators=investigators,
        outcomes=outcomes,
        eligibility=eligibility,
        contacts=contacts,
        results=results,
        raw=raw,
    )


def _sponsor_records(nct_id: str, module: Dict[str, Any]) -> List[SponsorRecord]:
    records: List[SponsorRecord] = []
    lead = module.get("leadSponsor")
    if lead:
        records.append(SponsorRecord(nct_id=nct_id, sponsor_type="LEAD", name=lead.get("name")))
    for collab in module.get("collaborators", []) or []:
        records.append(SponsorRecord(nct_id=nct_id, sponsor_type="COLLABORATOR", name=collab.get("name")))
    return records


def _mesh_records(nct_id: str, derived: Dict[str, Any]) -> List[MeshTermRecord]:
    records: List[MeshTermRecord] = []
    cond_module = derived.get("conditionBrowseModule") or {}
    for mesh in cond_module.get("meshes", []) or []:
        records.append(MeshTermRecord(nct_id=nct_id, term_type="condition", term=mesh.get("term")))
    for ancestor in cond_module.get("ancestors", []) or []:
        records.append(MeshTermRecord(nct_id=nct_id, term_type="condition_ancestor", term=ancestor.get("term")))
    inter_module = derived.get("interventionBrowseModule") or {}
    for mesh in inter_module.get("meshes", []) or []:
        records.append(MeshTermRecord(nct_id=nct_id, term_type="intervention", term=mesh.get("term")))
    return records


def _interventions(nct_id: str, module: Dict[str, Any]) -> List[InterventionRecord]:
    records: List[InterventionRecord] = []
    for item in module.get("interventions", []) or []:
        records.append(
            InterventionRecord(
                nct_id=nct_id,
                intervention_type=item.get("type"),
                name=item.get("name"),
                description=item.get("description"),
                arm_groups=list(item.get("armGroupLabels", []) or []),
            )
        )
    return records


def _arm_groups(nct_id: str, module: Dict[str, Any]) -> List[ArmGroupRecord]:
    records: List[ArmGroupRecord] = []
    for arm in module.get("armGroups", []) or []:
        records.append(
            ArmGroupRecord(
                nct_id=nct_id,
                label=arm.get("label"),
                description=arm.get("description"),
                type=arm.get("type"),
            )
        )
    return records


def _locations(nct_id: str, module: Dict[str, Any]) -> List[LocationRecord]:
    records: List[LocationRecord] = []
    for loc in module.get("locations", []) or []:
        records.append(
            LocationRecord(
                nct_id=nct_id,
                status=loc.get("status"),
                facility=loc.get("facility"),
                city=loc.get("city"),
                state=loc.get("state"),
                zip_code=loc.get("zip"),
                country=loc.get("country"),
            )
        )
    return records


def _investigators(nct_id: str, module: Dict[str, Any]) -> List[InvestigatorRecord]:
    records: List[InvestigatorRecord] = []
    for official in module.get("overallOfficials", []) or []:
        records.append(
            InvestigatorRecord(
                nct_id=nct_id,
                name=official.get("name"),
                role=official.get("role"),
                affiliation=official.get("affiliation"),
            )
        )
    return records


def _contacts(nct_id: str, module: Dict[str, Any]) -> List[ContactRecord]:
    records: List[ContactRecord] = []
    for contact in module.get("centralContacts", []) or []:
        records.append(
            ContactRecord(
                nct_id=nct_id,
                role=contact.get("role", "CENTRAL_CONTACT"),
                name=contact.get("name"),
                phone=contact.get("phone"),
                email=contact.get("email"),
            )
        )
    for contact in module.get("overallOfficials", []) or []:
        records.append(
            ContactRecord(
                nct_id=nct_id,
                role="OVERALL_OFFICIAL",
                name=contact.get("name"),
                phone=None,
                email=None,
            )
        )
    return records


def _outcomes(nct_id: str, module: Dict[str, Any]) -> List[OutcomeRecord]:
    records: List[OutcomeRecord] = []
    for item in module.get("primaryOutcomes", []) or []:
        records.append(
            OutcomeRecord(
                nct_id=nct_id,
                category="PRIMARY",
                measure=item.get("measure"),
                description=item.get("description"),
                time_frame=item.get("timeFrame"),
            )
        )
    for item in module.get("secondaryOutcomes", []) or []:
        records.append(
            OutcomeRecord(
                nct_id=nct_id,
                category="SECONDARY",
                measure=item.get("measure"),
                description=item.get("description"),
                time_frame=item.get("timeFrame"),
            )
        )
    for item in module.get("otherOutcomes", []) or []:
        records.append(
            OutcomeRecord(
                nct_id=nct_id,
                category="OTHER",
                measure=item.get("measure"),
                description=item.get("description"),
                time_frame=item.get("timeFrame"),
            )
        )
    return records


def _eligibility(nct_id: str, module: Dict[str, Any]) -> Optional[EligibilityRecord]:
    if not module:
        return None
    return EligibilityRecord(
        nct_id=nct_id,
        criteria=module.get("eligibilityCriteria"),
        gender=module.get("sex"),
        minimum_age=module.get("minimumAge"),
        maximum_age=module.get("maximumAge"),
        healthy_volunteers=str(module.get("healthyVolunteers")) if module.get("healthyVolunteers") is not None else None,
        population=module.get("studyPopulation"),
        sampling_method=module.get("samplingMethod"),
    )


def _result_events(nct_id: str, raw: Dict[str, Any]) -> List[ResultEventRecord]:
    records: List[ResultEventRecord] = []
    results_section = raw.get("resultsSection", {}) or {}
    outcome_measures = results_section.get("outcomeMeasuresModule", {}) or {}
    for measure in outcome_measures.get("outcomeMeasures", []) or []:
        title = measure.get("title") or measure.get("description")
        records.append(
            ResultEventRecord(
                nct_id=nct_id,
                event_type="OUTCOME_MEASURE",
                title=title,
                description=measure.get("description"),
            )
        )
    adverse_events = results_section.get("adverseEventsModule", {}) or {}
    for event in adverse_events.get("seriousEvents", []) or []:
        records.append(
            ResultEventRecord(
                nct_id=nct_id,
                event_type="SERIOUS_ADVERSE_EVENT",
                title=event.get("organSystem"),
                description=event.get("adverseEvent") or event.get("description"),
            )
        )
    for event in adverse_events.get("otherEvents", []) or []:
        records.append(
            ResultEventRecord(
                nct_id=nct_id,
                event_type="OTHER_ADVERSE_EVENT",
                title=event.get("organSystem"),
                description=event.get("adverseEvent") or event.get("description"),
            )
        )
    return records


def _date_from_struct(struct: Optional[Dict[str, Any]]) -> Optional[str]:
    if not struct:
        return None
    if isinstance(struct, dict):
        return struct.get("date") or struct.get("dateStruct")
    return None


def _first(value: Optional[Iterable[Any]]) -> Optional[str]:
    if not value:
        return None
    for item in value:
        if item:
            return str(item)
    return None


def _get(obj: Dict[str, Any], *keys: str) -> Optional[Any]:
    current: Any = obj
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_responsible_party(party: Optional[Dict[str, Any]]) -> Optional[str]:
    if not party:
        return None
    party_type = party.get("type")
    if party_type == "SPONSOR_INVESTIGATOR" or party_type == "PRINCIPAL_INVESTIGATOR":
        return f"{party_type}:{party.get('investigatorFullName')}"
    return party_type
