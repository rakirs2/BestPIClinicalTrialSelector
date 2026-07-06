"""Dataclasses representing normalized study records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional


@dataclass(slots=True)
class StudyRecord:
    nct_id: str
    brief_title: Optional[str]
    official_title: Optional[str]
    study_type: Optional[str]
    phase: Optional[str]
    enrollment: Optional[int]
    enrollment_type: Optional[str]
    overall_status: Optional[str]
    start_date: Optional[str]
    completion_date: Optional[str]
    primary_completion_date: Optional[str]
    last_update_post_date: Optional[str]
    last_changed_date: Optional[str]
    study_first_post_date: Optional[str]
    results_first_post_date: Optional[str]
    verification_date: Optional[str]
    study_model: Optional[str]
    masking: Optional[str]
    allocation: Optional[str]
    intervention_model: Optional[str]
    responsible_party: Optional[str]
    conditions_description: Optional[str]
    design_primary_purpose: Optional[str]
    biospec_retention: Optional[str]
    biospec_descr: Optional[str]
    last_refreshed_on: datetime


@dataclass(slots=True)
class SponsorRecord:
    nct_id: str
    sponsor_type: str
    name: str


@dataclass(slots=True)
class ConditionRecord:
    nct_id: str
    name: str


@dataclass(slots=True)
class KeywordRecord:
    nct_id: str
    keyword: str


@dataclass(slots=True)
class MeshTermRecord:
    nct_id: str
    term_type: str
    term: str


@dataclass(slots=True)
class InterventionRecord:
    nct_id: str
    intervention_type: Optional[str]
    name: Optional[str]
    description: Optional[str]
    arm_groups: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ArmGroupRecord:
    nct_id: str
    label: Optional[str]
    description: Optional[str]
    type: Optional[str]


@dataclass(slots=True)
class LocationRecord:
    nct_id: str
    status: Optional[str]
    facility: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]


@dataclass(slots=True)
class InvestigatorRecord:
    nct_id: str
    name: Optional[str]
    role: Optional[str]
    affiliation: Optional[str]


@dataclass(slots=True)
class OutcomeRecord:
    nct_id: str
    category: str
    measure: Optional[str]
    description: Optional[str]
    time_frame: Optional[str]


@dataclass(slots=True)
class EligibilityRecord:
    nct_id: str
    criteria: Optional[str]
    gender: Optional[str]
    minimum_age: Optional[str]
    maximum_age: Optional[str]
    healthy_volunteers: Optional[str]
    population: Optional[str]
    sampling_method: Optional[str]


@dataclass(slots=True)
class ContactRecord:
    nct_id: str
    role: str
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]


@dataclass(slots=True)
class ResultEventRecord:
    nct_id: str
    event_type: str
    title: Optional[str]
    description: Optional[str]


@dataclass(slots=True)
class NormalizedStudy:
    study: StudyRecord
    sponsors: List[SponsorRecord] = field(default_factory=list)
    conditions: List[ConditionRecord] = field(default_factory=list)
    keywords: List[KeywordRecord] = field(default_factory=list)
    mesh_terms: List[MeshTermRecord] = field(default_factory=list)
    interventions: List[InterventionRecord] = field(default_factory=list)
    arm_groups: List[ArmGroupRecord] = field(default_factory=list)
    locations: List[LocationRecord] = field(default_factory=list)
    investigators: List[InvestigatorRecord] = field(default_factory=list)
    outcomes: List[OutcomeRecord] = field(default_factory=list)
    eligibility: Optional[EligibilityRecord] = None
    contacts: List[ContactRecord] = field(default_factory=list)
    results: List[ResultEventRecord] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
