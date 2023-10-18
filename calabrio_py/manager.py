def retry(func):
    MAX_RETRIES = 5

    async def wrapper(*args, **kwargs):
        for retry in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                wait_time = 5**retry
                print(f"Error: {e}. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        return await func(*args, **kwargs)

    return wrapper


class ConfigManager:
    """
    This class is used to load the config data from the API and save it to a file
    (saving a file is optional. if you don't need to save, you can leave config_path blank).

    The config data is used to map the IDs to the names of the entities.
    """

    def __init__(self, client=None, config_path=None):
        self.client = client
        self.config_path = config_path
        self.config_data = None

    def get_client(self):
        return self.client

    async def get_async_client(self):
        if self.client.set_async:
            return self.client
        return None

    async def fetch_config_data(self):
        if self.config_path:
            try:
                with open(self.config_path) as file:
                    self.config_data = json.load(file)
            except FileNotFoundError:
                await self.create_config_from_api()
        else:
            self.config_data = await self.create_config_from_api()

    async def create_config_from_api(self, exclude_bu_names=[]):
        self.config_data = {"bus": []}
        client = self.get_client()

        if client:
            bus_list_res = (
                await client.get_all_business_units()
                if self.client.set_async
                else client.get_all_business_units()
            )
            bus_list = bus_list_res["Result"]
            for bu in bus_list:
                bu_name = bu["Name"] if bu["Name"] not in exclude_bu_names else None

                if bu_name is None:
                    continue

                bu_id = bu["Id"]
                self.config_data["bus"].append(bu)
                self.config_data[bu_name] = {}
                print(f"Fetching config data for {bu_name}...")

                api_methods = [
                    "get_all_sites",
                    "get_all_teams",
                    "get_all_skills",
                    "get_all_shift_bags",
                    "get_all_budget_groups",
                    "get_all_absences",
                    "get_all_activities",
                    "get_all_contracts",
                    "get_all_contract_schedules",
                    "get_all_workflow_control_sets",
                    "get_all_part_time_percentages",
                    "get_all_shift_categories",
                    "get_all_scenarios",
                    "get_all_roles",
                    "get_all_optional_column",
                ]

                for method_name in api_methods:
                    api_method = getattr(client, method_name)
                    config_key = method_name.split("get_all_")[
                        1
                    ]  # Get the config key name
                    self.config_data[bu_name][config_key] = (
                        await api_method(bu_id)
                        if self.client.set_async
                        else api_method(bu_id)
                    )

            if self.config_path:
                # Save to file
                with open(self.config_path, "w") as file:
                    json.dump(self.config_data, file)

            return self.config_data


import pandas as pd
import json
import numpy as np
import asyncio
from asyncio import Semaphore
from tqdm import tqdm
# from calabrio_api import AddPersonRequest


class PeopleManager:
    """
    This class is used to fetch the people data from the API and merge it with the config data.
    """

    def __init__(self, client, config_data=None):
        self.config_data = config_data
        if self.config_data is not None:
            business_units = self.config_data["bus"]
            self.bus_df = pd.DataFrame(business_units)
            self.bus_df.columns = ["BusinessUnitId", "BusinessUnitName"]
        self.client = client
        self.business_units = []
        self.people = []
        self.people_df = pd.DataFrame()
        self.sites = []
        self.teams = []
        self.absences = []
        self.contracts = []
        self.roles = []
        self.contract_schedules = []
        self.workflow_control_sets = []
        self.part_time_percentages = []
        self.shift_bags = []
        self.budget_groups = []
        self.shift_categories = []
        self.scenarios = []

        return None
    
    def __reduce__(self):
        return (self.__class__, (), self.__dict__)
    
    def __getstate__(self):
        return self.__dict__

    async def fetch_config_data(self, exclude_bu_names=[]):
        if self.config_data is None:
            self.config_manager = ConfigManager(self.client)
            if self.client.set_async:
                self.config_data = await self.config_manager.create_config_from_api(
                    exclude_bu_names=exclude_bu_names
                )
            else:
                self.config_data = await self.config_manager.create_config_from_api(
                    exclude_bu_names=exclude_bu_names
                )

    async def fetch_business_units(self):
        business_units_res = await self.client.get_all_business_units()
        self.business_units = business_units_res["Result"]

    async def fetch_teams_and_people_as_of_date(self, date, exclude_bu_names=[]):
        if len(self.business_units) == 0:
            await self.fetch_business_units()

        self.business_units = [
            bu for bu in self.business_units if bu["Name"] not in exclude_bu_names
        ]

        all_teams = await asyncio.gather(
            *[
                self.client.get_all_teams(bu["Id"])
                for bu in self.business_units
                if bu["Name"] not in exclude_bu_names
            ]
        )
        all_teams = [teams["Result"] for teams in all_teams]
        flatten_all_teams = [team for teams in all_teams for team in teams]

        all_people = await asyncio.gather(
            *[
                self.client.get_people_by_team_id(team["Id"], date)
                for team in flatten_all_teams
            ]
        )
        all_people = [people["Result"] for people in all_people]
        flatten_all_people = [person for people in all_people for person in people]

        return flatten_all_people

    async def fetch_all_people(
        self,
        date=None,
        include_eoy=False,
        with_ids=True,
        as_df=True,
        exclude_bu_names=[],
    ):
        if self.config_data is None:
            await self.fetch_config_data(
                exclude_bu_names=exclude_bu_names
            ) if self.client.set_async else self.fetch_config_data(
                exclude_bu_names=exclude_bu_names
            )

        # Assign today's date if date is None
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        # Fetch and process people data as of the given date
        as_of_date_data = await self.fetch_teams_and_people_as_of_date(
            date, exclude_bu_names=exclude_bu_names
        )
        as_of_date_df = pd.DataFrame(as_of_date_data)
        # Merge data and perform cleanup for as_of_date data

        self.people_df = self.merge_and_clean_data(as_of_date_df)

        # Fetch config and merge with as_of_date data
        [
            self.fetch_config_data_for_business_unit(bu["Name"])
            for bu in self.business_units
        ]
        self.fetch_config_data_as_df()

        # Merge the data for EOY if include_eoy is True
        if include_eoy:
            date = pd.to_datetime("today").strftime("%Y-12-31")
            flatten_all_people_eoy = await self.fetch_teams_and_people_as_of_date(date)
            all_people_eoy_df = pd.DataFrame(flatten_all_people_eoy)

            # Merge data and perform cleanup for EOY data
            all_people_eoy_df = self.merge_and_clean_data(all_people_eoy_df)

            # Merge EOY data and drop duplicates
            all_people_concat_df = pd.concat(
                [self.people_df, all_people_eoy_df], ignore_index=True
            )
            all_people_concat_df.drop_duplicates(
                subset=["BusinessUnitId", "EmploymentNumber"], inplace=True
            )

        # Merge data and perform necessary operations
        len(self.people_df)
        self.people_df = self.merge_and_filter_config_data()

        # Remove ids if not needed
        if not with_ids:
            self.people_df = self.people_df.drop(
                columns=[
                    "PersonId",
                    "BusinessUnitId",
                    "SiteId",
                    "TeamId",
                    "ContractId",
                    "WorkflowControlSetId",
                    "ContractId",
                    "ContractScheduleId",
                    "BudgetGroupId",
                    "PartTimePercentageId",
                    "ShiftBagId",
                ]
            )

        # Convert to dict if as_df is False
        if not as_df:
            all_people_dict = self.people_df.to_dict(orient="records")
            self.people = all_people_dict
            return all_people_dict

        return self.people_df

    async def fetch_people_by_employment_numbers(self, employment_numbers, date=None):
        if self.config_data is None:
            await self.fetch_config_data()

        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers, date
        )
        people = people_res["Result"]
        people_df = pd.DataFrame(people)

        # people_df = self.merge_and_filter_config_data(people_df)

        return people_df

    def merge_and_clean_data(self, people_df):
        # Concatenate and clean up the data
        people_df = people_df.drop_duplicates(
            subset=["BusinessUnitId", "EmploymentNumber"]
        )
        self.bus_df["BusinessUnitId"] = self.bus_df["BusinessUnitId"].astype(
            str
        )  # Convert to string type
        people_df = pd.merge(people_df, self.bus_df, on="BusinessUnitId", how="left")
        people_df.rename(columns={"Id": "PersonId"}, inplace=True)
        return people_df

    def fetch_config_data_as_df(self):
        self.sites_df = pd.concat(self.sites)
        self.sites_df.rename(columns={"Id": "SiteId", "Name": "SiteName"}, inplace=True)

        self.teams_df = pd.concat(self.teams)
        self.teams_df.rename(
            columns={"Id": "TeamId", "Name": "SiteTeamName"}, inplace=True
        )

        self.contracts_df = pd.concat(self.contracts)
        self.contracts_df.rename(
            columns={"Id": "ContractId", "Name": "ContractName"}, inplace=True
        )

        self.absences_df = pd.concat(self.absences)
        self.absences_df.rename(
            columns={"Id": "AbsenceId", "Name": "AbsenceName"}, inplace=True
        )

        self.roles_df = pd.concat(self.roles)
        self.roles_df.rename(columns={"Id": "RoleId", "Name": "RoleName"}, inplace=True)

        self.contract_schedules_df = pd.concat(self.contract_schedules)
        self.contract_schedules_df.rename(
            columns={"Id": "ContractScheduleId", "Name": "ContractScheduleName"},
            inplace=True,
        )

        self.workflow_control_sets_df = pd.concat(self.workflow_control_sets)
        self.workflow_control_sets_df.rename(
            columns={"Id": "WorkflowControlSetId", "Name": "WorkflowControlSetName"},
            inplace=True,
        )

        self.part_time_percentages_df = pd.concat(self.part_time_percentages)
        self.part_time_percentages_df.rename(
            columns={"Id": "PartTimePercentageId", "Name": "PartTimePercentageName"},
            inplace=True,
        )

        self.shift_bags_df = pd.concat(self.shift_bags)
        self.shift_bags_df.rename(
            columns={"Id": "ShiftBagId", "Name": "ShiftBagName"}, inplace=True
        )

        self.budget_groups_df = pd.concat(self.budget_groups)
        self.budget_groups_df.rename(
            columns={"Id": "BudgetGroupId", "Name": "BudgetGroupName"}, inplace=True
        )

        self.shift_categories_df = pd.concat(self.shift_categories)
        self.shift_categories_df.rename(
            columns={"Id": "ShiftCategoryId", "Name": "ShiftCategoryName"}, inplace=True
        )

        self.scenarios_df = pd.concat(self.scenarios)
        self.scenarios_df.rename(
            columns={"Id": "ScenarioId", "Name": "ScenarioName"}, inplace=True
        )

    def fetch_config_data_for_business_unit(self, bu_name):
        self.fetch_config(self.sites, "sites", bu_name)
        self.fetch_config(self.teams, "teams", bu_name)
        self.fetch_config(self.absences, "absences", bu_name)
        self.fetch_config(self.contracts, "contracts", bu_name)
        self.fetch_config(self.roles, "roles", bu_name)
        self.fetch_config(self.contract_schedules, "contract_schedules", bu_name)
        self.fetch_config(self.workflow_control_sets, "workflow_control_sets", bu_name)
        self.fetch_config(self.part_time_percentages, "part_time_percentages", bu_name)
        self.fetch_config(self.shift_bags, "shift_bags", bu_name)
        self.fetch_config(self.budget_groups, "budget_groups", bu_name)
        self.fetch_config(self.shift_categories, "shift_categories", bu_name)
        self.fetch_config(self.scenarios, "scenarios", bu_name)

    def fetch_config(self, data_list, key, bu_name):
        data_to_add = pd.DataFrame(self.config_data[bu_name][key]["Result"])
        data_to_add["BusinessUnitName"] = bu_name
        data_list.append(data_to_add)

    def merge_and_filter_config_data(self):
        self.people_df["BusinessUnitName"] = self.people_df["BusinessUnitName"].astype(
            str
        )
        self.people_df["RoleId"] = self.people_df["Roles"].apply(
            lambda x: self.get_first_role_id(x)
        )

        tmp_df = self.people_df.merge(
            self.sites_df, on=["SiteId", "BusinessUnitName"], how="left"
        )
        tmp_df = tmp_df.merge(
            self.teams_df,
            on=["TeamId", "SiteId", "SiteName", "BusinessUnitName"],
            how="left",
        )
        tmp_df = tmp_df.merge(
            self.contracts_df, on=["ContractId", "BusinessUnitName"], how="left"
        )
        tmp_df = tmp_df.merge(
            self.roles_df, on=["RoleId", "BusinessUnitName"], how="left"
        )
        self.people_df = tmp_df

        return self.people_df

    def get_first_role_id(self, role_list):
        if len(role_list) > 0:
            return role_list[0]["RoleId"]
        else:
            return None

    async def add_people_by_df(self, people_df):
        log = []

        # Define columns to merge and their corresponding DataFrame
        merge_columns = [
            ("TeamName", "BusinessUnitName", self.teams_df, "TeamId"),
            ("ContractName", "BusinessUnitName", self.contracts_df, "ContractId"),
            ("RoleName", "BusinessUnitName", self.roles_df, "RoleId"),
            ("BusinessUnitName", None, self.bus_df, "BusinessUnitId"),
            (
                "ContractScheduleName",
                "BusinessUnitName",
                self.contract_schedules_df,
                "ContractScheduleId",
            ),
            (
                "WorkflowControlSetName",
                "BusinessUnitName",
                self.workflow_control_sets_df,
                "WorkflowControlSetId",
            ),
            (
                "PartTimePercentageName",
                "BusinessUnitName",
                self.part_time_percentages_df,
                "PartTimePercentageId",
            ),
            # Add more merge columns as needed
        ]

        # Create dictionaries to store lookup values and their IDs
        lookup_dicts = {}

        # Batch the lookup operations
        for col1, col2, df, id_col in merge_columns:
            if id_col not in people_df.columns:
                if col1 in people_df.columns:
                    lookup_values = people_df[col1].unique()
                    if col2:
                        lookup_values_with_bu = people_df[
                            [col1, col2]
                        ].drop_duplicates()
                        for _, row in lookup_values_with_bu.iterrows():
                            lookup_values = lookup_values.append(
                                df[(df[col1] == row[col1]) & (df[col2] == row[col2])][
                                    id_col
                                ]
                            )
                    else:
                        lookup_values = people_df[col1].unique()
                    lookup_dicts[(col1, col2)] = dict(
                        zip(lookup_values, df.set_index(col1)[id_col])
                    )
                    people_df[id_col] = people_df.apply(
                        lambda x: lookup_dicts[(col1, col2)].get(x[col1])
                        if pd.notna(x[col1])
                        else None,
                        axis=1,
                    )

        # Loop through records and add people
        for person in people_df.to_dict(orient="records"):
            try:
                # Create the person request
                person_request = {
                    "TimeZoneId": person["TimeZoneId"],
                    "BusinessUnitId": person["BusinessUnitId"],
                    "FirstName": person["FirstName"],
                    "LastName": person["LastName"],
                    "StartDate": person["StartDate"],
                    "Email": person["Email"],
                    "EmploymentNumber": person["EmploymentNumber"],
                    "ApplicationLogon": person["ApplicationLogon"],
                    "Identity": person["Identity"],
                    "TeamId": person["TeamId"],
                    "ContractId": person["ContractId"],
                    "ContractScheduleId": person["ContractScheduleId"],
                    "PartTimePercentageId": person["PartTimePercentageId"],
                    "RoleIds": [person["RoleId"]] if person["RoleId"] else [],
                    "WorkflowControlSetId": person["WorkflowControlSetId"]
                    if "WorkflowControlSetId" in person
                    else "",
                    "ShiftBagId": person["ShiftBagId"]
                    if "ShiftBagId" in person
                    else "",
                    "BudgetGroupId": person["BudgetGroupId"]
                    if "BudgetGroupId" in person
                    else "",
                    "FirstDayOfWeek": person["FirstDayOfWeek"]
                    if "FirstDayOfWeek" in person
                    else 1,
                    "Culture": person["Culture"] if "Culture" in person else "",
                }

                print(person_request)

                # Add the person and append the result to the log
                res = await self.client.add_person(person_request)
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log.append([now, person["EmploymentNumber"], res])

            except Exception as e:
                # Handle the exception here, you can log it or take appropriate action
                print(f"An error occurred: {str(e)}")
                # You can choose to raise the exception again if needed
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log.append([now, person["EmploymentNumber"], str(e)])

        return log

    async def _switch_person_accessibility(
        self,
        person,
        date=None,
        remove=False,
        recover=False,
        activate=False,
        reset_new=False,
    ):
        log_entry = []
        now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")

        try:
            if remove and (person["TerminationDate"] is not None):
                email = "xxx" + person["Email"] if person["Email"] else None
                employment_number = (
                    "D" + person["EmploymentNumber"]
                    if person["EmploymentNumber"]
                    else None
                )
                identity = "xxx" + person["Identity"] if person["Identity"] else None
            elif recover:
                # If recovering, replace 'xxx' and 'D' with empty strings
                email = person["Email"].replace("xxx", "") if person["Email"] else None
                employment_number = (
                    person["EmploymentNumber"].replace("D", "")
                    if person["EmploymentNumber"]
                    else None
                )
                identity = (
                    person["Identity"].replace("xxx", "")
                    if person["Identity"]
                    else None
                )
            elif activate:
                # If activating, replace 'xxx' with empty strings
                email = person["Email"].replace("---", "") if person["Email"] else None
                employment_number = (
                    person["EmploymentNumber"].replace("N", "")
                    if person["EmploymentNumber"]
                    else None
                )
                identity = (
                    person["Identity"].replace("---", "")
                    if person["Identity"]
                    else None
                )
            elif reset_new:
                # If resetting new, replace 'xxx' and 'D' with empty strings
                email = "---" + person["Email"] if person["Email"] else None
                employment_number = (
                    "N" + person["EmploymentNumber"]
                    if person["EmploymentNumber"]
                    else None
                )
                identity = "---" + person["Identity"] if person["Identity"] else None
            else:
                print(
                    f"{person['Email']} in {person['BusinessUnitId']} is not terminated"
                )

            print(email, employment_number, identity)

            res = await self.client.set_details_for_person(
                person_id=person["Id"],
                email=email,
                employment_number=employment_number,
                identity=identity,
            )
            print(res)
            log_entry = [
                now,
                person["EmploymentNumber"],
                person["Email"],
                person,
                res,
                True,
            ]
        except Exception as e:
            error_message = f"Error processing person with ID {person['Id']}: {str(e)}"
            log_entry = [
                now,
                person["EmploymentNumber"],
                person["Email"],
                person,
                error_message,
                False,
            ]

        return log_entry

    async def remove_people_by_employment_numbers(self, employment_numbers, date=None):
        log = []
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers=employment_numbers, date=date
        )
        people = people_res["Result"]

        for person in people:
            try:
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log_entry = await self._switch_person_accessibility(person, remove=True)
                log.append(
                    [
                        now,
                        person["EmploymentNumber"],
                        person["Email"],
                        person,
                        log_entry,
                        True,
                    ]
                )
            except Exception as e:
                log.append(
                    [now, person["EmploymentNumber"], person["Email"], person, e, False]
                )

        return log

    async def recover_people_by_employment_numbers(self, employment_numbers, date=None):
        log = []
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers=employment_numbers, date=date
        )
        people = people_res["Result"]

        for person in people:
            try:
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log_entry = await self._switch_person_accessibility(
                    person, recover=True
                )
                log.append(
                    [
                        now,
                        person["EmploymentNumber"],
                        person["Email"],
                        person,
                        log_entry,
                        True,
                    ]
                )
            except Exception as e:
                log.append(
                    [now, person["EmploymentNumber"], person["Email"], person, e, False]
                )

        return log

    async def activate_people_by_employment_numbers(
        self, employment_numbers, date=None
    ):
        log = []
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers=employment_numbers, date=date
        )
        people = people_res["Result"]

        for person in people:
            try:
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log_entry = await self._switch_person_accessibility(
                    person, activate=True
                )
                log.append(
                    [
                        now,
                        person["EmploymentNumber"],
                        person["Email"],
                        person,
                        log_entry,
                        True,
                    ]
                )
            except Exception as e:
                log.append(
                    [now, person["EmploymentNumber"], person["Email"], person, e, False]
                )

        return log

    async def reset_new_people_by_employment_numbers(
        self, employment_numbers, date=None
    ):
        log = []
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers=employment_numbers, date=date
        )
        people = people_res["Result"]

        for person in people:
            try:
                now = pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")
                log_entry = await self._switch_person_accessibility(
                    person, reset_new=True
                )
                log.append(
                    [
                        now,
                        person["EmploymentNumber"],
                        person["Email"],
                        person,
                        log_entry,
                        True,
                    ]
                )
            except Exception as e:
                log.append(
                    [now, person["EmploymentNumber"], person["Email"], person, e, False]
                )

        return log

    async def set_termination_date_by_employment_number(
        self, employment_number, termination_date
    ):
        # get person_id by employment_number
        date = pd.to_datetime("today").strftime("%Y-%m-%d")
        people_res = await self.client.get_people_by_employment_numbers(
            employment_numbers=[employment_number], date=date
        )
        people = people_res["Result"]
        if len(people) == 0:
            return f"Employment number {employment_number} not found."

        person_id = people[0]["Id"]

        # set termination date
        res = await self.client.set_leaving_date_for_person(person_id, termination_date)

        return res

    async def find_employment_numbers_to_activate_today(self, date=None):
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")
        people_to_activate = self.people_df[
            self.people_df["EmploymentStartDate"] == date
        ]
        people_to_activate = people_to_activate[
            people_to_activate["EmploymentNumber"].str.startswith("N")
        ]
        employment_numbers = people_to_activate["EmploymentNumber"].tolist()

        return employment_numbers

    def get_one_day_before_start_date(self, employment_number):
        """
        This is to know the date to set as the termination date for a person who is starting in another business unit.
        """
        person = self.people_df[self.people_df["EmploymentNumber"] == employment_number]
        if len(person) == 0:
            return f"Employment number {employment_number} not found."
        one_day_before_start_date = pd.to_datetime(
            person["EmploymentStartDate"].values[0]
        ) - pd.Timedelta(days=1)
        return one_day_before_start_date.strftime("%Y-%m-%d")


class PersonAccountsManager:
    def __init__(self, people_mgr=None, client=None, people_df=None, config_data=None):
        if people_mgr:
            self.client = people_mgr.client
            self.people_mgr = people_mgr
            self.people_df = people_mgr.people_df
            self.config_data = people_mgr.config_data
        else:
            self.client = client
            self.people_df = people_df
            self.config_data = config_data

    async def fetch_config_data(self, exclude_bu_names=[]):
        if not hasattr(self, "config_data"):
            self.config_manager = ConfigManager(self.client)
            if self.client.set_async:
                self.config_data = await self.config_manager.create_config_from_api(
                    exclude_bu_names=exclude_bu_names
                )
            else:
                self.config_data = await self.config_manager.create_config_from_api(
                    exclude_bu_names=exclude_bu_names
                )

    def fetch_config(self, data_list, key, bu_name):
        data_to_add = pd.DataFrame(self.config_data[bu_name][key]["Result"])
        data_to_add["BusinessUnitName"] = bu_name
        data_list.append(data_to_add)

    async def fetch_config_data_as_df(self, exclude_bu_names=[]):
        await self.fetch_config_data(exclude_bu_names=exclude_bu_names)
        self.absences = []
        [
            self.fetch_config(self.absences, "absences", bu["Name"])
            for bu in self.config_data["bus"]
        ]
        self.absences_df = pd.concat(self.absences)
        self.absences_df.rename(
            columns={"Id": "AbsenceId", "Name": "AbsenceName"}, inplace=True
        )

    async def fetch_and_process_chunk(
        self, client, chunk, date, max_retry, max_concurrent
    ):
        semaphore = asyncio.Semaphore(max_concurrent)
        person_accounts_with_id = []

        async def fetch_single_person_account(business_unit_id, person_id, date):
            for retry in range(max_retry):
                try:
                    person_accounts = await client.get_person_accounts_by_person_id(
                        business_unit_id, person_id, date
                    )
                    # Extract the 'Result' list and add 'PersonId' to each dictionary
                    results = [
                        {"PersonId": person_id, **account}
                        for account in person_accounts.get("Result", [])
                    ]
                    return results
                except Exception as e:
                    # Handle any exceptions here, e.g., log an error
                    print(f"Error while processing PersonId {person_id}: {e}")
                    if retry == max_retry - 1:
                        return []  # Return an empty list to indicate a failure

                    await asyncio.sleep(10**retry)  # Exponential back-off

        fetch_tasks = [
            asyncio.ensure_future(
                fetch_single_person_account(
                    person_tuple["BusinessUnitId"], person_tuple["PersonId"], date
                )
            )
            for _, person_tuple in chunk.iterrows()
        ]

        async def process_results():
            for fetched_account in asyncio.as_completed(fetch_tasks):
                async with semaphore:
                    account_data = await fetched_account
                    if account_data:
                        person_accounts_with_id.extend(account_data)

        await process_results()
        return person_accounts_with_id

    async def fetch_person_accounts(
        self,
        date=None,
        people_df=None,
        client=None,
        with_id=False,
        details=False,
        max_retry=10,
        max_concurrent=200,
    ):
        if people_df is None:
            people_df = self.people_df

        people_df["BusinessUnitId"] = people_df["BusinessUnitId"].astype(str)

        if client is None:
            client = self.client

        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        person_accounts_with_id = []

        # Split people_df into chunks
        chunk_size = 200
        num_chunks = len(people_df) // chunk_size + 1

        # Create a tqdm object outside the loop
        progress_bar = tqdm(total=num_chunks, desc="Processing Chunks")

        for chunk_index in range(num_chunks):
            chunk_start = chunk_index * chunk_size
            chunk_end = (chunk_index + 1) * chunk_size
            chunk = people_df.iloc[chunk_start:chunk_end]

            # Fetch and process each chunk asynchronously
            chunk_results = await self.fetch_and_process_chunk(
                client, chunk, date, max_retry, max_concurrent
            )
            person_accounts_with_id.extend(chunk_results)

            # Update the progress bar for each chunk processed
            progress_bar.update(1)

        person_accounts_df = pd.DataFrame(person_accounts_with_id)
        if len(person_accounts_df) == 0:
            print("No person accounts found for the given date")
            return pd.DataFrame()

        # using people_df, add peoples' email and employment number to person_accounts on person_id
        person_accounts_df = person_accounts_df.merge(
            people_df[
                [
                    "BusinessUnitName",
                    "PersonId",
                    "Email",
                    "EmploymentNumber",
                    "ContractName",
                ]
            ],
            on="PersonId",
            how="left",
        )
        # load_config if absences_df is not defined
        if not hasattr(self, "absences_df"):
            await self.fetch_config_data()
            await self.fetch_config_data_as_df()

        # merge with absences_df

        person_accounts_df = person_accounts_df.merge(
            self.absences_df, on=["AbsenceId", "BusinessUnitName"], how="left"
        )
        person_accounts_df["StartDate"] = pd.to_datetime(
            person_accounts_df["Period"].apply(lambda x: x["StartDate"])
        )
        person_accounts_df["EndDate"] = pd.to_datetime(
            person_accounts_df["Period"].apply(lambda x: x["EndDate"])
        )
        person_accounts_df = person_accounts_df.drop(columns=["Period"])

        if not with_id:
            person_accounts_df = person_accounts_df.drop(
                columns=["PersonId", "AbsenceId"]
            )

        if not details:
            person_accounts_df = person_accounts_df.drop(
                columns=[
                    "Priority",
                    "Requestable",
                    "InWorkTime",
                    "InPaidTime",
                    "PayrollCode",
                    "Confidential",
                    "InContractTime",
                    "TrackerType",
                    "IsDeleted",
                ]
            )

        self.person_accounts_df = person_accounts_df

        return person_accounts_df

    async def fetch_person_accounts_by_bu_names(
        self, bu_names, date=None, with_id=False, details=False, max_concurrent=50
    ):
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_df = self.people_df[self.people_df["BusinessUnitName"].isin(bu_names)]
        person_accounts_df = await self.fetch_person_accounts(
            date,
            people_df,
            with_id=with_id,
            details=details,
            max_concurrent=max_concurrent,
        )
        return person_accounts_df

    async def fetch_person_accounts_by_team_names(
        self, team_names, date=None, with_id=False, details=False, max_concurrent=50
    ):
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_df = self.people_df[self.people_df["TeamName"].isin(team_names)]
        person_accounts_df = await self.fetch_person_accounts(
            date,
            people_df,
            with_id=with_id,
            details=details,
            max_concurrent=max_concurrent,
        )
        return person_accounts_df

    async def fetch_person_accounts_by_contract_names(
        self, contract_names, date=None, with_id=False, details=False, max_concurrent=50
    ):
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_df = self.people_df[self.people_df["ContractName"].isin(contract_names)]
        person_accounts_df = await self.fetch_person_accounts(
            date,
            people_df,
            with_id=with_id,
            details=details,
            max_concurrent=max_concurrent,
        )
        return person_accounts_df

    async def fetch_person_accounts_by_employment_numbers(
        self,
        employment_numbers,
        date=None,
        with_id=False,
        details=False,
        max_concurrent=50,
    ):
        if date is None:
            date = pd.to_datetime("today").strftime("%Y-%m-%d")

        people_df = self.people_df[
            self.people_df["EmploymentNumber"].isin(employment_numbers)
        ]
        person_accounts_df = await self.fetch_person_accounts(
            date,
            people_df,
            with_id=True,
            details=details,
            max_concurrent=max_concurrent,
        )
        person_accounts_df = person_accounts_df[
            [
                "BusinessUnitName",
                "ContractName",
                "EmploymentNumber",
                "Email",
                "AbsenceName",
                "StartDate",
                "EndDate",
                "BalanceIn",
                "Extra",
                "Accrued",
                "Used",
                "Remaining",
                "BalanceOut",
                "TrackedBy",
                "PersonId",
                "AbsenceId",
            ]
        ]
        return person_accounts_df

    async def add_or_update_person_accouts_by_employment_number_and_absence_name(
        self, employment_number, absence_name, balance_in=None, extra=None, accrued=None
    ):
        if not hasattr(self, "absences_df"):
            await self.fetch_config_data()
            await self.fetch_config_data_as_df()

        if not hasattr(self, "people_df"):
            await self.fetch_all_people()

        person_id = self.people_df[
            (self.people_df["EmploymentNumber"] == employment_number)
        ]["PersonId"].tolist()[0]

        absence_id = self.absences_df[
            (self.absences_df["AbsenceName"] == absence_name)
        ]["AbsenceId"].tolist()[0]

        # find existing person account for this person and absence
        person_accounts = self.fetch_person_accounts_by_employment_numbers(
            [employment_number], with_id=True
        )
        person_account = person_accounts[
            (person_accounts["AbsenceName"] == absence_name)
        ][0]

        # add PersonId and AbsenceId using people_df and self.absence_df if not present
        if (
            "PersonId" not in person_accounts[0].keys()
            or "AbsenceId" not in person_accounts[0].keys()
        ):
            person_accounts = [
                self.add_person_id_and_absence_id(account, self.people_df)
                for account in person_accounts
            ]

        # convert StartDate and EndDate to string
        person_accounts = [
            self.convert_date_to_string(account) for account in person_accounts
        ]

        person_accounts = await asyncio.gather(
            *[
                self.client.add_or_update_person_account_for_person(
                    person_account["PersonId"],
                    person_account["AbsenceId"],
                    person_account["StartDate"],
                    person_account["BalanceIn"],
                    person_account["Extra"],
                    person_account["Accrued"],
                )
                for person_account in person_accounts
            ]
        )
        return person_accounts

    def add_person_id_and_absence_id(self, account, people_df):
        person_id = people_df[
            (people_df["BusinessUnitName"] == account["BusinessUnitName"])
            & (people_df["EmploymentNumber"] == account["EmploymentNumber"])
        ]["PersonId"].tolist()[0]
        absence_id = self.absences_df[
            (self.absences_df["BusinessUnitName"] == account["BusinessUnitName"])
            & (self.absences_df["AbsenceName"] == account["AbsenceName"])
        ]["AbsenceId"].tolist()[0]
        account["PersonId"] = person_id
        account["AbsenceId"] = absence_id
        return account

    def convert_date_to_string(self, account):
        account["StartDate"] = account["StartDate"].strftime("%Y-%m-%d")
        account["EndDate"] = account["EndDate"].strftime("%Y-%m-%d")
        return account

    async def delete_person_accounts(self, accounts_df):
        log = []
        for index, row in accounts_df.iterrows():
            res = await self.client.delete_person_account(
                person_id=row["PersonId"],
                absence_id=row["AbsenceId"],
                date_from=row["StartDate"],
            )
        return log

    async def adhoc_update_person_account_by_employment_number(
        self, employment_number, absence_name, date_from, balance_in, extra, accrued
    ):
        person_id = self.people_df[
            self.people_df["EmploymentNumber"] == employment_number
        ]["PersonId"].iloc[0]
        bu_name = self.people_df[
            self.people_df["EmploymentNumber"] == employment_number
        ]["BusinessUnitName"].iloc[0]
        absence_id = self.absences_df[
            (self.absences_df["AbsenceName"] == absence_name)
            & (self.absences_df["BusinessUnitName"] == bu_name)
        ]["AbsenceId"].iloc[0]
        try:
            res = await self.client.add_or_update_person_account_for_person(
                person_id, absence_id, date_from, balance_in, extra, accrued
            )
            return res
        except Exception as e:
            print(person_id, absence_id, date_from, balance_in, extra, accrued)
            return f"Error for PersonId {person_id}: {e}"


class ScheduleManager:
    def __init__(self, people_mgr, people_df=None, config_data=None):
        self.client = people_mgr.client
        self.people_mgr = people_mgr
        if people_df is None:
            self.people_df = people_mgr.people_df
        else:
            self.people_df = people_df
        self.config_data = config_data
        self.fetch_activities_df()
        self.fetch_absences_df()

    def fetch_activities_df(self):
        self.activities_df = []
        for bu in self.people_mgr.bus_df.to_dict("records"):
            activities = self.people_mgr.config_data[bu["BusinessUnitName"]][
                "activities"
            ]["Result"]
            activities_df = pd.DataFrame(activities)
            activities_df["BusinessUnitName"] = bu["BusinessUnitName"]
            self.activities_df.append(activities_df)

        # flatten self.activities_df
        self.activities_df = pd.concat(self.activities_df)

        return self.activities_df

    def fetch_absences_df(self):
        self.absences_df = []
        for bu in self.people_mgr.bus_df.to_dict("records"):
            absences = self.people_mgr.config_data[bu["BusinessUnitName"]]["absences"][
                "Result"
            ]
            absences_df = pd.DataFrame(absences)
            absences_df["BusinessUnitName"] = bu["BusinessUnitName"]
            self.absences_df.append(absences_df)

        # flatten self.activities_df
        self.absences_df = pd.concat(self.absences_df)

        return self.absences_df

    def copy_first_shift_name(self, row):
        if pd.isna(row["ShiftCategoryId"]) and row["Shift"]:
            return row["Shift"][0]["Name"]
        else:
            return None

    async def get_all_schedules_in_all_bus(
        self, start_date, end_date, with_ids=False, as_df=True, max_concurrent=50
    ):
        try:
            # Get a list of unique business unit names
            bu_names = self.people_mgr.bus_df["BusinessUnitName"].unique()
            print(
                f"Fetching schedules for {bu_names} ... Please note that this list includes only the business units that have been set in the People Instance associated with this instance"
            )

            # Initialize a list to store schedules
            schedules = []

            # Create a semaphore to limit concurrent tasks
            semaphore = asyncio.Semaphore(max_concurrent)

            async def fetch_schedules(bu_name):
                async with semaphore:
                    result_df = await self.get_schedule_by_bu_name(
                        bu_name,
                        start_date,
                        end_date,
                        with_ids,
                        as_df=True,
                        max_concurrent=max_concurrent,
                    )
                    if not result_df.empty:
                        schedules.append(result_df)

            # Fetch schedules one by one
            for bu_name in bu_names:
                await fetch_schedules(bu_name)

            # Consolidate schedules into a single DataFrame if needed
            if as_df:
                if schedules:
                    return pd.concat(schedules, ignore_index=True)
                else:
                    return pd.DataFrame()
            else:
                return schedules
        except Exception as e:
            # Handle exceptions here
            print(f"An error occurred: {str(e)}")

    async def get_schedule_by_bu_name(
        self,
        bu_name,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        max_concurrent=50,
    ):
        try:
            # Fetch schedules for team
            employment_numbers = self.people_mgr.people_df[
                self.people_mgr.people_df["BusinessUnitName"] == bu_name
            ]["EmploymentNumber"].values

            return await self.get_schedule_by_employment_numbers(
                employment_numbers,
                start_date,
                end_date,
                with_ids,
                as_df=True,
                max_concurrent=max_concurrent,
            )

        except Exception as error:
            print("Error occurred in get_schedule_by_bu_name:", error)
            return pd.DataFrame()

    async def _fetch_schedule_data(
        self, team_id, bu_id, start_date, end_date, max_retries=3
    ):
        retries = 0

        while retries < max_retries:
            try:
                schedules_res = await self.client.get_schedule_by_team_id(
                    bu_id, team_id, start_date, end_date
                )
                schedules = schedules_res["Result"]
                return pd.DataFrame(schedules)

            except Exception as error:
                print(f"Error occurred (Attempt {retries + 1}/{max_retries}):", error)
                retries += 1
                if retries < max_retries:
                    # Calculate the wait time using exponential backoff (e.g., 2^retry_count seconds)
                    wait_time = 2**retries
                    print(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        print("Maximum number of retries reached. Returning an empty DataFrame.")
        return pd.DataFrame()

    def _process_schedule_dataframe(self, schedules_df, with_ids=False):
        try:
            print("Processing schedule data...")
            schedules_df["ShiftCategoryId"] = schedules_df["ShiftCategory"].apply(
                lambda x: x["Id"] if x is not None else None
            )
            schedules_df["ShiftCategoryName"] = schedules_df["ShiftCategory"].apply(
                lambda x: x["Name"] if x is not None else None
            )
            schedules_df["ShiftCategoryShortName"] = schedules_df[
                "ShiftCategory"
            ].apply(lambda x: x["ShortName"] if x is not None else None)
            schedules_df.drop(columns=["ShiftCategory"], inplace=True)
            schedules_df["DayOffName"] = schedules_df["DayOff"].apply(
                lambda x: x["Name"] if x is not None else None
            )
            schedules_df["AbsenceName"] = schedules_df.apply(
                self.copy_first_shift_name, axis=1
            )
            schedules_df["StartTime"] = schedules_df.apply(
                lambda x: pd.to_datetime(x["Shift"][0]["Period"]["StartTime"])
                if x["Shift"]
                else None,
                axis=1,
            )
            schedules_df["EndTime"] = schedules_df.apply(
                lambda x: pd.to_datetime(x["Shift"][-1]["Period"]["EndTime"])
                if x["Shift"]
                else None,
                axis=1,
            )
            schedules_df["Duration"] = (
                schedules_df["EndTime"] - schedules_df["StartTime"]
            )
            schedules_df["Name"] = (
                schedules_df["ShiftCategoryShortName"]
                .fillna(schedules_df["AbsenceName"])
                .fillna(schedules_df["DayOffName"])
            )

            org_info_df = self.people_df[
                [
                    "PersonId",
                    "BusinessUnitName",
                    "TeamName",
                    "EmploymentNumber",
                    "Email",
                ]
            ]
            schedules_df = schedules_df.merge(org_info_df, on="PersonId", how="left")

            schedules_df = schedules_df[
                [
                    "BusinessUnitName",
                    "TeamName",
                    "Date",
                    "StartTime",
                    "EndTime",
                    "Duration",
                    "Name",
                    "PersonId",
                    "Email",
                    "EmploymentNumber",
                    "ShiftCategoryId",
                    "ShiftCategoryName",
                    "ShiftCategoryShortName",
                    "DayOffName",
                    "AbsenceName",
                ]
            ]
            schedules_df = schedules_df[~schedules_df["Name"].isna()]
            if not with_ids:
                schedules_df.drop(columns=["PersonId", "ShiftCategoryId"], inplace=True)

            return schedules_df
        except Exception as error:
            print("Error occurred in _process_schedule_dataframe:", error)
            return pd.DataFrame()

    async def get_schedule_by_team_name(
        self, team_name, start_date, end_date, with_ids=False, as_df=True, max_retries=3
    ):
        try:
            teams = self.people_mgr.teams_df
            team_id = teams[teams["TeamName"] == team_name]["TeamId"].values[0]
            bu_name = teams[teams["TeamName"] == team_name]["BusinessUnitName"].values[
                0
            ]
            bus = self.people_mgr.bus_df
            bu_id = bus[bus["BusinessUnitName"] == bu_name]["BusinessUnitId"].values[0]

            schedules_df = await self._fetch_schedule_data(
                team_id, bu_id, start_date, end_date, max_retries
            )

            if not schedules_df.empty:
                self.schedules_df = self._process_schedule_dataframe(
                    schedules_df, with_ids
                )

                if as_df:
                    return self.schedules_df
                else:
                    return self.schedules_df.to_dict("records")
            else:
                # print("No data retrieved. Returning an empty list.")
                return []

        except Exception as error:
            print(f"Error occurred in get_schedule_by_team_name:", error)
            return []

    async def process_schedule_chunk(self, chunk, start_date, end_date):
        schedule_task = {"Result": []}
        # try:
        person_ids = self.people_mgr.people_df[
            self.people_mgr.people_df["EmploymentNumber"].isin(chunk)
        ]["PersonId"].values
        person_ids = list(person_ids)
        if len(person_ids) == 0:
            print('No person ids found for the given employment numbers')
            return {"Result":[]}
        # Await the asynchronous function here
        schedule_task = await self.client.get_schedule_by_person_ids(
            person_ids, start_date, end_date
        )
        if len(schedule_task['Errors']) > 0:
            raise Exception(schedule_task['Errors'])
        
        print(schedule_task)

        return schedule_task
        # except Exception as error:
        #     print("Error occurred in process_schedule_chunk:", error)
        #     print(chunk)
        #     return {"Result":[]}

    async def get_schedule_by_employment_numbers(
        self,
        employment_numbers,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        date_of_view=None,
        max_concurrent=50,
    ):
        # split into chunks
        chunks = [
            employment_numbers[i : i + 200]
            for i in range(0, len(employment_numbers), 200)
        ]

        schedule_tasks = []
        try:
            semaphore = asyncio.Semaphore(max_concurrent)  # Create a semaphore

            for i, chunk in enumerate(chunks):
                async with semaphore:
                    schedule_task = asyncio.ensure_future(
                        self.process_schedule_chunk(chunk, start_date, end_date)
                    )
                    schedule_tasks.append(schedule_task)

                    # Calculate progress manually
                    progress = (i + 1) / len(chunks) * 100

            # Gather the tasks
            schedules_res_list = await asyncio.gather(*schedule_tasks)
            schedules_list = [
                schedules_res["Result"] for schedules_res in schedules_res_list
            ]
            flattened_schedules = [
                schedule for sublist in schedules_list for schedule in sublist
            ]


            if len(flattened_schedules) > 0:
                if as_df:
                    schedules_df = pd.DataFrame(flattened_schedules)
                    self.schedules_df = self._process_schedule_dataframe(
                        schedules_df, with_ids
                    )
                    return self.schedules_df
                else:
                    return flattened_schedules
            else:
                print("No data retrieved. Returning an empty list.")
                return []

        except Exception as error:
            print("Error occurred in get_schedule_by_employment_numbers: ", error)
            return pd.DataFrame()

    async def get_all_schedule_activities_in_all_bus(
        self,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        with_duration=False,
        max_concurrent=50,
        query=None,
    ):
        try:
            # Get a list of unique business unit names
            employment_numbers = self.people_mgr.people_df["EmploymentNumber"].unique()

            # Initialize a list to store schedule activities
            schedules_activities = (
                await self.get_schedule_activities_by_employment_numbers(
                    employment_numbers,
                    start_date,
                    end_date,
                    with_ids,
                    as_df=True,
                    with_duration=with_duration,
                    max_concurrent=max_concurrent,
                    query=query,
                )
            )
            print("schedule fetched")
            return schedules_activities

        except Exception as error:
            # If an error occurs during the process, print the error and return an empty list.
            print("Error occurred in get_all_schedule_activities_in_all_bus:", error)
            return pd.DataFrame()

    async def get_schedule_activities_by_bu_name(
        self,
        bu_names,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        with_duration=False,
        max_concurrent=50,
        query=None,
    ):
        try:
            # Fetch schedules for the specified team and date range.
            employment_numbers = self.people_mgr.people_df[
                self.people_mgr.people_df["BusinessUnitName"].isin(bu_names)
            ]["EmploymentNumber"].values

            schedules_activities = (
                await self.get_schedule_activities_by_employment_numbers(
                    employment_numbers,
                    start_date,
                    end_date,
                    with_ids,
                    as_df=True,
                    with_duration=with_duration,
                    max_concurrent=max_concurrent,
                    query=query,
                )
            )

            return schedules_activities

        except Exception as error:
            # If an error occurs during the process, print the error and return an empty DataFrame.
            print("Error occurred in get_schedule_activities_by_bu_name:", error)
            return pd.DataFrame()

    async def get_schedule_activities(
        self, schedules, with_ids=False, as_df=True, with_duration=False, query=None
    ):
        try:
            schedule_activities = self.extract_activities(schedules, query)

            if not schedule_activities:
                return []

            schedule_activities_df = self.convert_activities_to_dataframe(
                schedule_activities
            )
            org_info_df = self.people_df[
                [
                    "PersonId",
                    "BusinessUnitName",
                    "TeamName",
                    "EmploymentNumber",
                    "Email",
                ]
            ]
            schedule_activities_df = schedule_activities_df.merge(
                org_info_df, on="PersonId", how="left"
            )

            if with_duration:
                schedule_activities_df["Duration"] = (
                    schedule_activities_df["EndTime"]
                    - schedule_activities_df["StartTime"]
                )
                cols = [
                    "BusinessUnitName",
                    "TeamName",
                    "Date",
                    "StartTime",
                    "EndTime",
                    "Duration",
                    "ActivityName",
                    "PersonId",
                    "Email",
                    "EmploymentNumber",
                    "Overtime",
                    "ActivityId",
                    "AbsenceId",
                ]
            else:
                cols = [
                    "BusinessUnitName",
                    "TeamName",
                    "Date",
                    "StartTime",
                    "EndTime",
                    "ActivityName",
                    "PersonId",
                    "Email",
                    "EmploymentNumber",
                    "Overtime",
                    "ActivityId",
                    "AbsenceId",
                ]

            schedule_activities_df = schedule_activities_df[cols]

            if not with_ids:
                schedule_activities_df.drop(
                    columns=["PersonId", "ActivityId", "AbsenceId"], inplace=True
                )

            return (
                schedule_activities_df
                if as_df
                else schedule_activities_df.to_dict("records")
            )

        except Exception as error:
            print("Error occurred in converting schedules into activities df:", error)
            return []

    def extract_activities(self, schedules, query):
        return [
            {**activity, "PersonId": schedule["PersonId"], "Date": schedule["Date"]}
            for schedule in schedules
            if "Shift" in schedule
            for activity in schedule["Shift"]
            if not query or all(activity.get(k) == v for k, v in query.items())
        ]

    def convert_activities_to_dataframe(self, activities):
        df = pd.DataFrame(activities)
        df.rename(columns={"Name": "ActivityName"}, inplace=True)
        df["StartTime"] = df["Period"].apply(lambda x: pd.to_datetime(x["StartTime"]))
        df["EndTime"] = df["Period"].apply(lambda x: pd.to_datetime(x["EndTime"]))
        df.drop(columns=["Period"], inplace=True)
        return df

    async def get_schedule_activities_by_team_name(
        self,
        team_name,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        with_duration=False,
        max_retries=3,
        query=None,
    ):
        retries = 0

        while retries < max_retries:
            try:
                teams = self.people_mgr.teams_df
                team_id = teams[teams["TeamName"] == team_name]["TeamId"].values[0]
                bu_name = teams[teams["TeamName"] == team_name][
                    "BusinessUnitName"
                ].values[0]
                bus = self.people_mgr.bus_df
                bu_id = bus[bus["BusinessUnitName"] == bu_name][
                    "BusinessUnitId"
                ].values[0]

                schedules_res = await self.client.get_schedule_by_team_id(
                    bu_id, team_id, start_date, end_date
                )
                schedules = schedules_res["Result"]
                self.schedules = schedules

                return await self.get_schedule_activities(
                    schedules, with_ids, as_df, with_duration, query=query
                )

            except Exception as error:
                print(
                    f"Error occurred in get_schedule_activities_by_team_name (Attempt {retries + 1}/{max_retries}):",
                    error,
                )
                retries += 1
                if retries < max_retries:
                    # Calculate the wait time using exponential backoff (e.g., 2^retry_count seconds)
                    wait_time = 2**retries
                    print(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        print("Maximum number of retries reached. Returning an empty list.")
        return []

    async def get_schedule_activities_by_employment_numbers(
        self,
        employment_numbers,
        start_date,
        end_date,
        with_ids=False,
        as_df=True,
        date_of_view=None,
        with_duration=False,
        max_concurrent=50,
        query=None,
    ):
        try:
            schedules = await self.get_schedule_by_employment_numbers(
                employment_numbers,
                start_date,
                end_date,
                with_ids=True,
                as_df=False,
                date_of_view=date_of_view,
                max_concurrent=max_concurrent,
            )
            print("schedules fetched")
            return await self.get_schedule_activities(
                schedules, with_ids, as_df, with_duration, query=query
            )

        except Exception as error:
            print(
                "Error occurred in get_schedule_activities_by_employment_numbers:",
                error,
            )
            return pd.DataFrame()

    def count_overtime_hours_by_name(self, df, overtime_name):
        df = df[df["Overtime"] == overtime_name]
        df["Duration"] = df["EndTime"] - df["StartTime"]
        df["Duration"] = df["Duration"].apply(lambda x: x.total_seconds() / 3600)

        # group by person
        df = (
            df.groupby(["BusinessUnitName", "TeamName", "EmploymentNumber", "Email"])
            .sum()
            .reset_index()
        )
        return df
