# Documentation

## Methods

### add_full_day_absence
- business_unit_id (str)
- person_id (str)
- date (str) - ISO 8601 date
- absence_id (str)
- scenario_id (str, optional)

### add_full_day_absence_request
- business_unit_id (str)
- person_id (str)
- date (str) - ISO 8601 date
- absence_id (str)
- scenario_id (str)

### add_intraday_absence_request
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 start date and time
- end_date (str) - ISO 8601 end date and time
- absence_id (str)
- subject (str)
- message (str)

### add_meetings
- time_zone_id (str)
- business_unit_id (str)
- scenario_id (str)
- external_meetings (List[ExternalMeeting])
- handle_non_overwritable_activities (bool)

#### *ExternalMeeting
    - ExternalMeetingId (str) - ID of the external meeting
    - Period (dict) - Period/timespan for the meeting
      - StartDate (str) - ISO 8601 start date and time
      - EndDate (str) - ISO 8601 end date and time
    - Participants (list) - List of participant IDs (strings)
    - ActivityId (str, optional) - Activity ID for the meeting
  - Title (str, optional) - Title of the meeting
  - Location (str, optional) - Location of the meeting
  - Agenda (str, optional) - Agenda text for the meeting

### add_or_update_person_account_for_person
- person_id (str)
- absence_id (str)
- date_from (str) - ISO 8601 date
- balance_in (float)
- extra (float)
- accrued (float)

### add_overtime
- time_zone_id (str)
- business_unit_id (str)
- person_id (str)
- start_time (str) - ISO 8601 datetime
- end_time (str) - ISO 8601 datetime
- activity_id (str)
- multiplicator_definition_set_id (str)
- scenario_id (str)

### add_overtime_request
- time_zone_id (str)
- business_unit_id (str)
- person_id (str)
- start_time (datetime)
- end_time (datetime)
- subject (str)
- message (str)
- overtime_type (str)

### add_part_day_absence
- time_zone_id (str)
- business_unit_id (str)
- person_id (str)
- start_time (datetime)
- end_time (datetime)
- absence_id (str)
- scenario_id (str)
- convert_if_applicable_for_full_day (bool)

### add_person
- add_person_request (AddPersonRequest)

#### *AddPersonRequest
    - TimeZoneId (str) - Time zone ID
    - BusinessUnitId (str) - Business unit ID
    - FirstName (str)
    - LastName (str)
    - StartDate (str) - ISO 8601 date
    - Email (str)
    - EmploymentNumber (str)
    - ApplicationLogon (str)
    - Identity (str)
    - TeamId (str)
    - ContractId (str)
    - ContractScheduleId (str)
    - PartTimePercentageId (str)
    - RoleIds (List[str]) - List of role IDs
    - WorkflowControlSetId (str)
    - ShiftBagId (str)
    - BudgetGroupId (str)
    - FirstDayOfWeek (int)
    - Culture (str)

### add_skills_to_person
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- skill_ids (List[str])

### add_team
- business_unit_id (str)
- team_name (str)
- site_id (str)

### clear_leaving_date_for_person
- person_id (str)

### edit_meetings
- time_zone_id (str)
- external_meetings (List[ExternalMeeting])

### import_backlog_queue
- queue_id (str)
- queue_name (str)
- tasks (List[dict])
- upload_id (str)

### process_backlog_queue- 
(no parameters)

### remove_full_day_absence
- business_unit_id (str)
- person_id (str)
- period (dict) - Date period
- startDate (str) - ISO 8601 start date
- endDate (str) - ISO 8601 end date
- scenario_id (str, optional)

### remove_meetings
- external_meeting_ids (List[str])

### remove_overtime_request
- time_zone_id (str)
- business_unit_id (str)
- person_id (str)
- start_time (str) - ISO 8601 datetime
- end_time (str) - ISO 8601 datetime
- scenario_id (str)

### remove_part_day_absence
- time_zone_id (str)
- business_unit_id (str)
- person_id (str)
- start_time (datetime)
- end_time (datetime)
- scenario_id (str)
- absence_ids (List[str])

### remove_skills_for_person
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- skill_ids (List[str])

### set_availability
- business_unit_id (str)
- person_id (str)
- availability_id (str)
- start_date (str) - ISO 8601 date

### set_bud
get_group_for_person
- business_unit_id (str)
- start_date (str) - ISO 8601 date
- person_id (str)
- budget_group_id (str)

### set_details_for_person
- person_id (str)
- first_name (str)
- last_name (str)
- email (str)
- workflow_control_set_id (str)
- note (str)
- employment_number (str)
- identity (str)

### set_employment_details_for_person
- business_unit_id (str)
- start_date (str) - ISO 8601 date
- person_id (str)
- contract_id (str)
- contract_schedule_id (str)
- part_time_percentage_id (str)
- team_id (str)

### set_external_logons_for_person
- person_id (str)
- date (str) - ISO 8601 date
- external_logon_ids (List[str])

### set_forecast
- business_unit_id (str)
- skill_id (str)
- scenario_id (str)
- days (List[ForecastDay])

#### *ForecastDay
    - Date (str) - ISO 8601 date
    - Intervals (List[ForecastInterval]) - List of forecast intervals

##### *ForecastInterval
    - Tasks (int) - Number of forecasted tasks
    - AverageTaskTimeSeconds (int) - Average task time in seconds
    - AverageAfterTaskTimeSeconds (int) - Average after-task time in seconds
    - AgentsOverride (int) - Override value for number of agents
    - StartTimeUtc (str) - Start time in ISO 8601 format

### set_leaving_date_for_person
- person_id (str)
- date (str) - ISO 8601 date

### set_location
- business_unit_id (str)
- person_ids (List[str])
- period (dict) - Date period
- startDate (str) - ISO 8601 start date
- endDate (str) - ISO 8601 end date
- location (str)

### set_optional_column_for_person
- person_id (str)
- optional_column_id (str)
- value (str)

### set_roles_for_person
- person_id (str)
- role_ids (List[str])

### set_rotation
- business_unit_id (str)
- person_id (str)
- rotation_id (str)
- start_date (str) - ISO 8601 date
- start_week (int)

### set_schedules_for_person
- options (SetSchedulesForPersonOptions)

#### SetSchedulesForPersonOptions
- timeZoneId (str)
- businessUnitId (str)
- datePeriod (dict) - Date period
  - startDate (str) - ISO 8601 start date
  - endDate (str) - ISO 8601 end date
- scheduleDays (List[dict]) - List of schedule days
- date (str) - ISO 8601 date
- shiftCategoryId (str)
- dayOffTemplateId (str)
- fullDayAbsenceId (str)
- layers (List[dict]) - List of schedule layers
  - period (dict) - Period for layer
    - startTime (str) - ISO 8601 start time
    - endTime (str) - ISO 8601 end time
  - activityId (str)
  - absenceId (str)
- personId (str)
- scenarioId (str)

### set_shift_bag_for_person
- business_unit_id (str)
- start_date (str) - ISO 8601 date
- person_id (str)
- shift_bag_id (str)

### set_shrinkage
- request_data (dict) - Request body data

### set_skills_for_person
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- skill_ids (List[str])

### set_team_for_person
- business_unit_id (str)
- start_date (str) - ISO 8601 date
- team_id (str)
- person_id (str)

### get_all_absences
- business_unit_id (str)
- filter (dict) - Filter criteria

### get_absence_possibility_by_person_id
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date

### get_absence_request_by_id
- business_unit_id (str)
- request_id (str)

### get_absence_request_rules_by_person_id
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date

### get_activities
- business_unit_id (str)
- filter (dict) - Filter criteria

### get_permission_by_person
- business_unit_id (str)
- person_id (str)

### get_all_availabilities
- business_unit_id (str)

### get_all_budget_groups
- business_unit_id (str)

### get_all_business_units
- (no parameters)

### get_all_contracts
- business_unit_id (str)

### get_all_contract_schedules
- business_unit_id (str)

### get_day_off_templates
- business_unit_id (str)

### get_employee_defaults
- business_unit_id (str)

### get_external_logon_by_id
- id (str)

### get_external_logons_by_data_source
- data_source_id (str)

### get_external_logons_by_person
- person_id (str)
- date (str) - ISO 8601 date

### get_forecast_by_skill
- business_unit_id (str)
- skill_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date
- apply_shrinkage (bool)
- scenario_id (str, optional)

### get_locations_by_person_ids
- business_unit_id (str)
- person_ids (List[str])
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date

### get_multiplicator_definition_sets
- business_unit_id (str)

### get_nightly_rest_by_person_id
- person_id (str)
- date (str) - ISO 8601 date

### query_optional_column
- business_unit_id (str)
- optional_query_parameters (dict, optional) - Optional query parameters

### get_overtime_possibility_by_person_id
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date

### get_overtime_request_configuration_by_person_id
- business_unit_id (str)
- person_id (str)
- date (str) - ISO 8601 date

### get_overtime_request_by_id
- business_unit_id (str)
- request_id (str)

### get_all_part_time_percentages
- business_unit_id (str)

### get_person_accounts_by_person_id
- business_unit_id (str)
- person_id (str)
- date (str) - ISO 8601 date

### get_people_by_employment_numbers
- employment_numbers (List[str])
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_people_by_group_page_group
- business_unit_id (str)
- group_page_group_id (str)
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_people_by_identities
- identities (List[str])
- date (str) - ISO 8601 date

### 
get_people_by_ids
- ids (List[str])
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_people_by_skill_group
- skill_group_id (str)
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_people_by_team_id
- team_id (str)
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_person_by_id
- person_id (str)
- date (str) - ISO 8601 date
- include_optional_columns (bool, optional)

### get_roles
- business_unit_id (str)

### get_all_rotations
- business_unit_id (str)

### query_scenario
- business_unit_id (str)

### schedule_absences_by_person_ids
- person_ids (List[str])
- period (dict) - Date period
- startDate (str) - ISO 8601 start date
- endDate (str) - ISO 8601 end date
- scenario_id (str, optional)

### query_schedule_audit_trail_by_person_id
- person_id (str)
- date (str) - ISO 8601 date

### get_schedules_by_change_date
- changes_from (datetime)
- changes_to (datetime)
- page (int)
- page_size (int)
- business_unit_id (str, optional)
- start_date (str, optional) - ISO 8601 date
- end_date (str, optional) - ISO 8601 date

### schedule_by_person_id
- person_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date
- scenario_id (str, optional)

### schedule_by_person_ids
- person_ids (List[str])
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date
- scenario_id (str, optional)

### get_schedule_by_team_id
- business_unit_id (str)
- team_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date
- scenario_id (str, optional)

### query_schedule_by_group_page_groups
- business_unit_id (str)
- group_page_group_ids (List[str])
- period (dict) - Date period
- startDate (str) - ISO 8601 start date
- endDate (str) - ISO 8601 end date
- scenario_id (str, optional)

### get_shift_bags
- business_unit_id (str)

### get_all_shift_categories
- business_unit_id (str)

### query_all_sites
- business_unit_id (str)

### get_all_skills
- business_unit_id (str)

### get_skill_groups
- business_unit_id (str)

### get_staffing_by_skills
- business_unit_id (str)
- skill_ids (List[str])
- start_time (datetime)
- end_time (datetime)

### get_all_teams
- business_unit_id (str)

### get_all_teams_with_agents
- business_unit_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date

### get_team_by_id
- id (str)

### get_teams_by_site_id
- business_unit_id (str)
- site_id (str)

### get_user_by_id
- person_id (str)

### get_workflow_control_sets
- business_unit_id (str)

### get_work_time_by_person_id
- business_unit_id (str)
- person_id (str)
- start_date (str) - ISO 8601 date
- end_date (str) - ISO 8601 date
- scenario_id (str, optional)
