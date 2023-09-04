import requests
import aiohttp
import asyncio
from requests.exceptions import RequestException
from datetime import datetime
from typing import List, Dict, Any


class ExternalMeeting:
    def __init__(self, ExternalMeetingId: str, Period: Dict[str, Any], Participants: List[str], ActivityId: str = None, Title: str = None, Location: str = None, Agenda: str = None) -> None:
        self.ExternalMeetingId = ExternalMeetingId
        self.Period = Period
        self.Participants = Participants
        self.ActivityId = ActivityId
        self.Title = Title
        self.Location = Location
        self.Agenda = Agenda


class AddPersonRequest:
    def __init__(self, TimeZoneId: str, BusinessUnitId: str, FirstName: str, LastName: str, StartDate: str, Email: str, EmploymentNumber: str, ApplicationLogon: str, Identity: str, TeamId: str, ContractId: str, ContractScheduleId: str, PartTimePercentageId: str, RoleIds: List[str], WorkflowControlSetId: str, ShiftBagId: str, BudgetGroupId: str, FirstDayOfWeek: int, Culture: str) -> None:
        self.TimeZoneId = TimeZoneId
        self.BusinessUnitId = BusinessUnitId
        self.FirstName = FirstName
        self.LastName = LastName
        self.StartDate = StartDate
        self.Email = Email
        self.EmploymentNumber = EmploymentNumber
        self.ApplicationLogon = ApplicationLogon
        self.Identity = Identity
        self.TeamId = TeamId
        self.ContractId = ContractId
        self.ContractScheduleId = ContractScheduleId
        self.PartTimePercentageId = PartTimePercentageId
        self.RoleIds = RoleIds
        self.WorkflowControlSetId = WorkflowControlSetId
        self.ShiftBagId = ShiftBagId
        self.BudgetGroupId = BudgetGroupId
        self.FirstDayOfWeek = FirstDayOfWeek
        self.Culture = Culture


class ForecastDay:
    def __init__(self, Date: str, Intervals: List['ForecastInterval']) -> None:
        self.Date = Date
        self.Intervals = Intervals


class ForecastInterval:
    def __init__(self, Tasks: int, AverageTaskTimeSeconds: int, AverageAfterTaskTimeSeconds: int, AgentsOverride: int, StartTimeUtc: str) -> None:
        self.Tasks = Tasks
        self.AverageTaskTimeSeconds = AverageTaskTimeSeconds
        self.AverageAfterTaskTimeSeconds = AverageAfterTaskTimeSeconds
        self.AgentsOverride = AgentsOverride
        self.StartTimeUtc = StartTimeUtc


class SetSchedulesForPersonOptions:
    def __init__(self, timeZoneId: str, businessUnitId: str, datePeriod: Dict[str, str], scheduleDays: List[Dict[str, Any]], personId: str, scenarioId: str) -> None:
        self.timeZoneId = timeZoneId
        self.businessUnitId = businessUnitId
        self.datePeriod = datePeriod
        self.scheduleDays = scheduleDays
        self.personId = personId
        self.scenarioId = scenarioId


class ApiClientBase:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.is_async = False

    def set_async(self, async_mode=True):
        self.is_async = async_mode

    def make_request_sync(self, method, url, **kwargs):
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def make_request_async(self, method, url, **kwargs):
        async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {self.api_key}"}) as session:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    def make_request(self, method, url, **kwargs):
        if self.is_async:
            return self.make_request_async(method, url, **kwargs)
        else:
            return self.make_request_sync(method, url, **kwargs)

    def get(self, url, params=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        return self.make_request("GET", self.base_url + url, headers=headers, params=params)

    def post(self, url, data=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        return self.make_request("POST", self.base_url + url, headers=headers, json=data)

    def get_all_commands(self):
        url = f"{self.base_url}/command"
        return self.get(url)

    def add_full_day_absence(self, business_unit_id, person_id, date, absence_id, scenario_id=None):
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Date": date,
            "AbsenceId": absence_id,
        }
        if scenario_id:
            request_data["ScenarioId"] = scenario_id
        url = f"{self.base_url}/command/AddFullDayAbsence"
        return self.post(url, request_data)

    def add_full_day_absence_request(self, business_unit_id, person_id, date, absence_id, scenario_id):
        url = f"{self.base_url}/command/AddFullDayAbsenceRequest"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Date": date,
            "AbsenceId": absence_id,
            "ScenarioId": scenario_id,
        }
        return self.post(url, request_data)

    def add_intraday_absence_request(self, business_unit_id, person_id, start_date, end_date, absence_id, subject, message):
        url = f"{self.base_url}/command/AddIntradayAbsenceRequest"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date,
            },
            "AbsenceId": absence_id,
            "Subject": subject,
            "Message": message,
        }
        return self.post(url, request_data)

    def add_meetings(self, time_zone_id, business_unit_id, scenario_id, external_meetings, handle_non_overwritable_activities):
        url = f"{self.base_url}/command/AddMeetings"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "ScenarioId": scenario_id,
            "ExternalMeetings": external_meetings,
            "HandleNonOverwritableActivities": handle_non_overwritable_activities
        }
        return self.post(url, request_data)

    def add_or_update_person_account_for_person(self, person_id, absence_id, date_from, balance_in, extra, accrued):
        url = f"{self.base_url}/command/AddOrUpdatePersonAccountForPerson"
        request_data = {
            "PersonId": person_id,
            "AbsenceId": absence_id,
            "DateFrom": date_from,
            "BalanceIn": balance_in,
            "Extra": extra,
            "Accrued": accrued
        }
        return self.post(url, request_data)

    def add_overtime(self, time_zone_id, business_unit_id, person_id, start_time, end_time, activity_id, multiplicator_definition_set_id, scenario_id):
        url = f"{self.base_url}/command/AddOvertime"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartTime": start_time,
                "EndTime": end_time
            },
            "ActivityId": activity_id,
            "MultiplicatorDefinitionSetId": multiplicator_definition_set_id,
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def delete_person_account(self, person_id, absence_id, date_from):
        url = f"{self.base_url}/command/DeleteAccountForPersonAccount"
        request_data = {
            "PersonId": person_id,
            "AbsenceId": absence_id,
            "DateFrom": date_from
        }
        return self.post(url, request_data)

    def add_overtime_request(self, time_zone_id, business_unit_id, person_id, start_time, end_time, subject, message, overtime_type):
        url = f"{self.base_url}/command/AddOvertimeRequest"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat()
            },
            "Subject": subject,
            "Message": message,
            "OvertimeType": overtime_type
        }
        return self.post(url, request_data)

    def add_part_day_absence(self, time_zone_id, business_unit_id, person_id, start_time, end_time, absence_id, scenario_id, convert_if_applicable_for_full_day):
        url = f"{self.base_url}/command/AddPartDayAbsence"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat()
            },
            "AbsenceId": absence_id,
            "ScenarioId": scenario_id,
            "ConvertIfApplicableForFullDay": convert_if_applicable_for_full_day
        }
        return self.post(url, request_data)

    def add_person(self, add_person_request: AddPersonRequest):
        url = f"{self.base_url}/command/AddPerson"
        return self.post(url, add_person_request)

    def add_skills_to_person(self, business_unit_id, person_id, start_date, skill_ids):
        url = f"{self.base_url}/command/AddSkillsToPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "StartDate": start_date,
            "SkillIds": skill_ids
        }
        return self.post(url, request_data)

    def add_team(self, business_unit_id, team_name, site_id):
        url = f"{self.base_url}/command/AddTeam"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "TeamName": team_name,
            "SiteId": site_id
        }
        return self.post(url, request_data)

    def clear_leaving_date_for_person(self, person_id):
        url = f"{self.base_url}/command/ClearLeavingDateForPerson"
        request_data = {
            "PersonId": person_id
        }
        return self.post(url, request_data)

    def edit_meetings(self, time_zone_id, external_meetings: List[ExternalMeeting]):
        url = f"{self.base_url}/command/EditMeetings"
        request_data = {
            "TimeZoneId": time_zone_id,
            "ExternalMeetings": external_meetings
        }
        return  self.post(url, request_data)
    
    def import_backlog_queue(self, queue_id, queue_name, tasks, upload_id):
        url = f"{self.base_url}/command/ImportBacklogQueue"
        request_data = {
            "QueueId": queue_id,
            "QueueName": queue_name,
            "Tasks": tasks,
            "UploadId": upload_id
        }
        return self.post(url, request_data)

    def process_backlog_queue(self):
        url = f"{self.base_url}/command/ProcessBacklogQueue"
        request_data = {}
        return self.post(url, request_data)

    def remove_full_day_absence(self, business_unit_id, person_id, period, scenario_id=None):
        url = f"{self.base_url}/command/RemoveFullDayAbsence"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": period["startDate"],
                "EndDate": period["endDate"]
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def remove_meetings(self, external_meeting_ids):
        url = f"{self.base_url}/command/RemoveMeetings"
        request_data = {
            "ExternalMeetingIds": external_meeting_ids
        }
        return self.post(url, request_data)
    
    def remove_overtime_request(self, time_zone_id, business_unit_id, person_id, start_time, end_time, scenario_id):
        url = f"{self.base_url}/command/RemoveOvertime"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartTime": start_time,
                "EndTime": end_time
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def remove_part_day_absence(self, time_zone_id, business_unit_id, person_id, start_time, end_time, scenario_id, absence_ids):
        url = f"{self.base_url}/command/RemovePartDayAbsence"
        request_data = {
            "TimeZoneId": time_zone_id,
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat()
            },
            "ScenarioId": scenario_id,
            "AbsenceIds": absence_ids
        }
        return self.post(url, request_data)

    def remove_skills_for_person(self, business_unit_id, person_id, start_date, skill_ids):
        url = f"{self.base_url}/command/RemoveSkillsForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "StartDate": start_date,
            "SkillIds": skill_ids
        }
        return self.post(url, request_data)
    
    def set_availability(self, business_unit_id, person_id, availability_id, start_date):
        url = f"{self.base_url}/command/SetAvailability"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "AvailabilityId": availability_id,
            "StartDate": start_date
        }
        return self.post(url, request_data)

    def set_budget_group_for_person(self, business_unit_id, start_date, person_id, budget_group_id):
        url = f"{self.base_url}/command/SetBudgetGroupForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "StartDate": start_date,
            "PersonId": person_id,
            "BudgetGroupId": budget_group_id
        }
        return self.post(url, request_data)

    def set_details_for_person(self, person_id, first_name, last_name, email, workflow_control_set_id, note, employment_number, identity):
        url = f"{self.base_url}/command/SetDetailsForPerson"
        request_data = {
            "PersonId": person_id,
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "WorkflowControlSetId": workflow_control_set_id,
            "Note": note,
            "EmploymentNumber": employment_number,
            "Identity": identity
        }
        return self.post(url, request_data)

    def set_employment_details_for_person(self, business_unit_id, start_date, person_id, contract_id, contract_schedule_id, part_time_percentage_id, team_id):
        url = f"{self.base_url}/command/SetEmploymentDetailsForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "StartDate": start_date,
            "PersonId": person_id,
            "ContractId": contract_id,
            "ContractScheduleId": contract_schedule_id,
            "PartTimePercentageId": part_time_percentage_id,
            "TeamId": team_id
        }
        return self.post(url, request_data)
    
    def set_external_logons_for_person(self, person_id, date, external_logon_ids):
        url = f"{self.base_url}/command/SetExternalLogonsForPerson"
        request_data = {
            "PersonId": person_id,
            "Date": date,
            "ExternalLogonIds": external_logon_ids
        }
        return self.post(url, request_data)

    def set_forecast(self, business_unit_id, skill_id, scenario_id, days):
        url = f"{self.base_url}/command/SetForecast"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "SkillId": skill_id,
            "ScenarioId": scenario_id,
            "Days": days
        }
        return self.post(url, request_data)

    def set_leaving_date_for_person(self, person_id, date):
        url = f"{self.base_url}/command/SetLeavingDateForPerson"
        request_data = {
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)

    def set_location(self, business_unit_id, person_ids, period, location):
        url = f"{self.base_url}/command/SetLocation"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonIds": person_ids,
            "Period": {
                "StartDate": period["startDate"],
                "EndDate": period["endDate"]
            },
            "Location": location
        }
        return self.post(url, request_data)
    
    def set_optional_column_for_person(self, person_id, optional_column_id, value):
        url = f"{self.base_url}/command/SetOptionalColumnForPerson"
        request_data = {
            "PersonId": person_id,
            "OptionalColumnId": optional_column_id,
            "Value": value
        }
        return self.post(url, request_data)

    def set_roles_for_person(self, person_id, role_ids):
        url = f"{self.base_url}/command/SetRolesForPerson"
        request_data = {
            "PersonId": person_id,
            "RoleIds": role_ids
        }
        return self.post(url, request_data)

    def set_rotation(self, business_unit_id, person_id, rotation_id, start_date, start_week):
        url = f"{self.base_url}/command/SetRotation"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "RotationId": rotation_id,
            "StartDate": start_date,
            "StartWeek": start_week
        }
        return self.post(url, request_data)

    def set_schedules_for_person(self, options: SetSchedulesForPersonOptions):
        url = f"{self.base_url}/command/SetSchedulesForPerson"
        request_data = {
            "TimeZoneId": options.timeZoneId,
            "BusinessUnitId": options.businessUnitId,
            "DatePeriod": {
                "StartDate": options.datePeriod.startDate,
                "EndDate": options.datePeriod.endDate
            },
            "ScheduleDays": [
                {
                    "Date": day.date,
                    "ShiftCategoryId": day.shiftCategoryId,
                    "DayOffTemplateId": day.dayOffTemplateId,
                    "FullDayAbsenceId": day.fullDayAbsenceId,
                    "Layers": [
                        {
                            "Period": {
                                "StartTime": layer.period.startTime,
                                "EndTime": layer.period.endTime
                            },
                            "ActivityId": layer.activityId,
                            "AbsenceId": layer.absenceId
                        } for layer in day.layers
                    ]
                } for day in options.scheduleDays
            ],
            "PersonId": options.personId,
            "ScenarioId": options.scenarioId
        }
        return self.post(url, request_data)
    
    def set_shift_bag_for_person(self, business_unit_id, start_date, person_id, shift_bag_id):
        url = f"{self.base_url}/command/SetShiftBagForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "StartDate": start_date,
            "PersonId": person_id,
            "ShiftBagId": shift_bag_id
        }
        return self.post(url, request_data)

    def set_shrinkage(self, request_data):
        url = f"{self.base_url}/command/SetShrinkage"
        return self.post(url, request_data)

    def set_skills_for_person(self, business_unit_id, person_id, start_date, skill_ids):
        url = f"{self.base_url}/command/SetSkillsForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "StartDate": start_date,
            "SkillIds": skill_ids
        }
        return self.post(url, request_data)

    def set_team_for_person(self, business_unit_id, start_date, team_id, person_id):
        url = f"{self.base_url}/command/SetTeamForPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "StartDate": start_date,
            "TeamId": team_id,
            "PersonId": person_id
        }
        return self.post(url, request_data)

    def get_all_absences(self, business_unit_id, filter=0):
        url = f"{self.base_url}/query/Absence/AllAbsences"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "Filter": filter
        }
        return self.post(url, request_data)
    
    def get_absence_possibility_by_person_id(self, business_unit_id, person_id, start_date, end_date):
        url = f"{self.base_url}/query/AbsencePossibility/AbsencePossibilityByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            }
        }
        return self.post(url, request_data)

    def get_absence_request_by_id(self, business_unit_id, request_id):
        url = f"{self.base_url}/query/AbsenceRequest/AbsenceRequestById"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "RequestId": request_id
        }
        return self.post(url, request_data)

    def get_absence_request_rules_by_person_id(self, business_unit_id, person_id, start_date, end_date):
        url = f"{self.base_url}/query/AbsenceRequestRule/AbsenceRequestRulesByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            }
        }
        return self.post(url, request_data)

    def get_all_activities(self, business_unit_id, filter=0):
        url = f"{self.base_url}/query/Activity/AllActivities"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "Filter": filter
        }
        return self.post(url, request_data)
    
    def get_permission_by_person(self, business_unit_id, person_id):
        url = f"{self.base_url}/query/ApplicationFunction/PermissionByPerson"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id
        }
        return self.post(url, request_data)

    def get_all_availabilities(self, business_unit_id):
        url = f"{self.base_url}/query/Availability/AllAvailabilities"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_budget_groups(self, business_unit_id):
        url = f"{self.base_url}/query/BudgetGroup/AllBudgetGroups"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_business_units(self):
        url = f"{self.base_url}/query/BusinessUnit/AllBusinessUnits"
        request_data = {}
        return self.post(url, request_data)

    def get_all_contracts(self, business_unit_id):
        url = f"{self.base_url}/query/Contract/AllContracts"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_contract_schedules(self, business_unit_id):
        url = f"{self.base_url}/query/ContractSchedule/AllContractSchedules"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)
    
    def get_day_off_templates(self, business_unit_id):
        url = f"{self.base_url}/query/DayOffTemplate/AllDayOffTemplates"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_employee_defaults(self, business_unit_id):
        url = f"{self.base_url}/query/EmployeeDefaults/GetEmployeeDefaults"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_external_logon_by_id(self, id):
        url = f"{self.base_url}/query/ExternalLogon/ExternalLogonById"
        request_data = {
            "Id": id
        }
        return self.post(url, request_data)

    def get_external_logons_by_data_source(self, data_source_id):
        url = f"{self.base_url}/query/ExternalLogon/ExternalLogonsByDataSource"
        request_data = {
            "DataSourceId": data_source_id
        }
        return self.post(url, request_data)
    
    def get_external_logons_by_person(self, person_id, date):
        url = f"{self.base_url}/query/ExternalLogon/ExternalLogonsByPerson"
        request_data = {
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)

    def get_forecast_by_skill(self, business_unit_id, skill_id, start_date, end_date, apply_shrinkage, scenario_id=None):
        url = f"{self.base_url}/query/Forecast/ForecastBySkill"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "SkillId": skill_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            },
            "ApplyShrinkage": apply_shrinkage,
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def get_locations_by_person_ids(self, business_unit_id, person_ids, start_date, end_date):
        url = f"{self.base_url}/query/Location/LocationsByPersonIds"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonIds": person_ids,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            }
        }
        return self.post(url, request_data)
    
    def get_multiplicator_definition_sets(self, business_unit_id):
        url = f"{self.base_url}/query/MultiplicatorDefinitionSet/AllMultiplicatorDefinitionSets"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_nightly_rest_by_person_id(self, person_id, date):
        url = f"{self.base_url}/query/NightlyRest/NightlyRestByPersonId"
        request_data = {
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)

    def get_all_optional_column(self, business_unit_id, optional_query_parameters=None):
        url = f"{self.base_url}/query/OptionalColumn/AllOptionalColumns"
        if optional_query_parameters:
            url += "?"
            url += "&".join([f"{key}={value}" for key, value in optional_query_parameters.items()])
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_overtime_possibility_by_person_id(self, business_unit_id, person_id, start_date, end_date):
        url = f"{self.base_url}/query/OvertimePossibility/OvertimePossibilityByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            }
        }
        return self.post(url, request_data)
    
    def get_overtime_request_configuration_by_person_id(self, business_unit_id, person_id, date):
        url = f"{self.base_url}/query/OvertimeRequestConfiguration/OvertimeRequestConfigurationByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)

    def get_overtime_request_by_id(self, business_unit_id, request_id):
        url = f"{self.base_url}/query/OvertimeRequest/OvertimeRequestById"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "RequestId": request_id
        }
        return self.post(url, request_data)

    def get_all_part_time_percentages(self, business_unit_id):
        url = f"{self.base_url}/query/PartTimePercentage/AllPartTimePercentages"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_person_accounts_by_person_id(self, business_unit_id, person_id, date):
        url = f"{self.base_url}/query/PersonAccount/PersonAccountsByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)
    
    def get_people_by_employment_numbers(self, employment_numbers, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleByEmploymentNumbers"
        request_data = {
            "EmploymentNumbers": employment_numbers,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)

    def get_people_by_group_page_group(self, business_unit_id, group_page_group_id, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleByGroupPageGroup"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "GroupPageGroupId": group_page_group_id,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)

    def get_people_by_identities(self, identities, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleByIdentities"
        request_data = {
            "Identities": identities,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)
    
    def get_people_by_ids(self, ids, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleByIds"
        request_data = {
            "Ids": ids,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)

    def get_people_by_skill_group(self, skill_group_id, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleBySkillGroup"
        request_data = {
            "SkillGroupId": skill_group_id,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)

    def get_people_by_team_id(self, team_id, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PeopleByTeamId"
        request_data = {
            "TeamId": team_id,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)

    def get_person_by_id(self, person_id, date, include_optional_columns=False):
        url = f"{self.base_url}/query/Person/PersonById"
        request_data = {
            "PersonId": person_id,
            "Date": date,
            "Include": {
                "OptionalColumns": include_optional_columns
            }
        }
        return self.post(url, request_data)
    
    def get_all_roles(self, business_unit_id):
        url = f"{self.base_url}/query/Role/AllRoles"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "GetApplicationFunctionsAndAvailableData": False
        }
        return self.post(url, request_data)

    def get_all_rotations(self, business_unit_id):
        url = f"{self.base_url}/query/Rotation/AllRotations"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_scenarios(self, business_unit_id):
        url = f"{self.base_url}/query/Scenario/AllScenarios"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def schedule_absences_by_person_ids(self, person_ids, period, scenario_id=None):
        url = f"{self.base_url}/query/ScheduleAbsence/ScheduleAbsencesByPersonIds"
        request_data = {
            "PersonIds": person_ids,
            "Period": {
                "StartDate": period["startDate"],
                "EndDate": period["endDate"]
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)
    
    def query_schedule_audit_trail_by_person_id(self, person_id, date):
        url = f"{self.base_url}/query/ScheduleAuditTrail/ScheduleAuditTrailByPersonId"
        request_data = {
            "PersonId": person_id,
            "Date": date
        }
        return self.post(url, request_data)

    def get_schedules_by_change_date(self, changes_from, changes_to, page, page_size,
                                     business_unit_id=None, start_date=None, end_date=None):
        url = f"{self.base_url}/query/ScheduleChanges/SchedulesByChangeDate"
        params = {
            "ChangesFrom": changes_from,
            "ChangesTo": changes_to,
            "Page": page,
            "PageSize": page_size,
            "BusinessUnitId": business_unit_id,
            "period.StartDate": start_date,
            "period.EndDate": end_date
        }
        response = self.get(url, params=params)
        return response.json()

    def schedule_by_person_id(self, person_id, start_date, end_date, scenario_id=None):
        url = f"{self.base_url}/query/Schedule/ScheduleByPersonId"
        request_data = {
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)
    
    def schedule_by_person_ids(self, person_ids, start_date, end_date, scenario_id=None):
        url = f"{self.base_url}/query/Schedule/ScheduleByPersonIds"
        request_data = {
            "PersonIds": person_ids,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def get_schedule_by_team_id(self, business_unit_id, team_id, start_date, end_date, scenario_id=None):
        url = f"{self.base_url}/query/Schedule/ScheduleByTeamId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "TeamId": team_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)

    def query_schedule_by_group_page_groups(self, business_unit_id, group_page_group_ids, period, scenario_id=None):
        url = f"{self.base_url}/query/ScheduleByGroupPageGroups"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "GroupPageGroupIds": group_page_group_ids,
            "Period": {
                "StartDate": period["startDate"],
                "EndDate": period["endDate"]
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)
    
    def get_all_shift_bags(self, business_unit_id):
        url = f"{self.base_url}/query/ShiftBag/AllShiftBags"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_shift_categories(self, business_unit_id):
        url = f"{self.base_url}/query/ShiftCategory/AllShiftCategories"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_sites(self, business_unit_id):
        url = f"{self.base_url}/query/Site/AllSites"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_all_skills(self, business_unit_id):
        url = f"{self.base_url}/query/Skill/AllSkills"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_skill_groups(self, business_unit_id):
        url = f"{self.base_url}/query/SkillGroup/AllSkillGroups"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_staffing_by_skills(self, business_unit_id, skill_ids, start_time, end_time):
        url = f"{self.base_url}/query/Staffing/StaffingBySkills"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "SkillIds": skill_ids,
            "Period": {
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat(),
            }
        }
        return self.post(url, request_data)

    def get_all_teams(self, business_unit_id):
        url = f"{self.base_url}/query/Team/AllTeams"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)
    
    def get_all_teams_with_agents(self, business_unit_id, start_date, end_date):
        url = f"{self.base_url}/query/Team/AllTeamsWithAgents"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date,
            }
        }
        return self.post(url, request_data)

    def get_team_by_id(self, id):
        url = f"{self.base_url}/query/Team/TeamById"
        request_data = {
            "Id": id
        }
        return self.post(url, request_data)

    def get_teams_by_site_id(self, business_unit_id, site_id):
        url = f"{self.base_url}/query/Team/TeamsBySiteId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "SiteId": site_id
        }
        return self.post(url, request_data)
    
    def get_user_by_id(self, person_id):
        url = f"{self.base_url}/query/User/UserById"
        request_data = {
            "PersonId": person_id
        }
        return self.post(url, request_data)

    def get_all_workflow_control_sets(self, business_unit_id):
        url = f"{self.base_url}/query/WorkflowControlSet/AllWorkflowControlSets"
        request_data = {
            "BusinessUnitId": business_unit_id
        }
        return self.post(url, request_data)

    def get_work_time_by_person_id(self, business_unit_id, person_id, start_date, end_date, scenario_id=None):
        url = f"{self.base_url}/query/WorkTime/WorkTimeByPersonId"
        request_data = {
            "BusinessUnitId": business_unit_id,
            "PersonId": person_id,
            "Period": {
                "StartDate": start_date,
                "EndDate": end_date,
            },
            "ScenarioId": scenario_id
        }
        return self.post(url, request_data)


class ApiClient(ApiClientBase):
    def __init__(self, base_url, api_key):
        super().__init__(base_url, api_key)

class AsyncApiClient(ApiClientBase):
    def __init__(self, base_url, api_key):
        super().__init__(base_url, api_key)
        self.set_async(True)
