import pandas as pd
import json
import asyncio
from tqdm import tqdm

class ConfigManager:
    '''
    This class is used to load the config data from the API and save it to a file 
    (saving a file is optional. if you don't need to save, you can leave config_path blank).
    
    The config data is used to map the IDs to the names of the entities.
    '''

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
            bus_list_res = await client.get_all_business_units() if self.client.set_async else client.get_all_business_units()
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
                    "get_all_sites", "get_all_teams", "get_all_skills",
                    "get_all_shift_bags", "get_all_budget_groups", "get_all_absences",
                    "get_all_activities", "get_all_contracts", "get_all_contract_schedules",
                    "get_all_workflow_control_sets", "get_all_part_time_percentages",
                    "get_all_shift_categories", "get_all_scenarios", "get_all_roles",
                    "get_all_optional_column"
                ]

                for method_name in api_methods:
                    api_method = getattr(client, method_name)
                    config_key = method_name.split("get_all_")[1]  # Get the config key name
                    self.config_data[bu_name][config_key] = await api_method(bu_id) if self.client.set_async else api_method(bu_id)

            if self.config_path:
                # Save to file
                with open(self.config_path, "w") as file:
                    json.dump(self.config_data, file)

            return self.config_data


import pandas as pd
import json


class PeopleManager:
    '''
    This class is used to fetch the people data from the API and merge it with the config data.
    '''
    def __init__(self, client, config_data=None):
        self.config_data = config_data
        self.client = client
        self.business_units = []
        self.people = []
        self.sites = []
        self.teams = []
        self.absences = []
        self.contracts = []
        self.roles = []

        return None

    async def fetch_config_data(self, exclude_bu_names=[]):
        if self.config_data is None:
            self.config_manager = ConfigManager(self.client)
            if self.client.set_async:
                self.config_data = await self.config_manager.create_config_from_api(exclude_bu_names=exclude_bu_names)
            else:
                self.config_data = await self.config_manager.create_config_from_api(exclude_bu_names=exclude_bu_names)

    async def fetch_business_units(self):
        business_units_res = await self.client.get_all_business_units()
        self.business_units = business_units_res['Result']

    async def fetch_teams_and_people_as_of_date(self, date, exclude_bu_names=[]):
        if (len(self.business_units)==0):
            await self.fetch_business_units()

        self.business_units = [bu for bu in self.business_units if bu['Name'] not in exclude_bu_names]

        all_teams = await asyncio.gather(
            *[self.client.get_all_teams(bu['Id']) for bu in self.business_units if bu['Name'] not in exclude_bu_names]
        )
        all_teams = [teams['Result'] for teams in all_teams]
        flatten_all_teams = [team for teams in all_teams for team in teams]


        all_people = await asyncio.gather(
            *[self.client.get_people_by_team_id(team['Id'], date) for team in flatten_all_teams]
        )
        all_people = [people['Result'] for people in all_people]
        flatten_all_people = [person for people in all_people for person in people]

        return flatten_all_people

    async def fetch_all_people(self, date=None, include_eoy=False, with_ids=False, as_df=True, exclude_bu_names=[]):
        if self.config_data is None:
            await self.fetch_config_data(exclude_bu_names=exclude_bu_names) if self.client.set_async else self.fetch_config_data(exclude_bu_names=exclude_bu_names)

        # Assign today's date if date is None
        if date is None:
            date = pd.to_datetime('today').strftime('%Y-%m-%d')

        business_units = self.config_data['bus']
        self.bus_df = pd.DataFrame(business_units)
        self.bus_df.columns=['BusinessUnitId', 'BusinessUnitName']
 
        # Fetch and process people data as of the given date
        as_of_date_data = await self.fetch_teams_and_people_as_of_date(date, exclude_bu_names=exclude_bu_names)
        as_of_date_df = pd.DataFrame(as_of_date_data)
        # Merge data and perform cleanup for as_of_date data
       
        self.people_df = self.merge_and_clean_data(as_of_date_df)

        # Fetch config and merge with as_of_date data
        [self.fetch_config_data_for_business_unit(bu['Name']) for bu in business_units]
        self.fetch_config_data_as_df()

        # Merge the data for EOY if include_eoy is True
        if include_eoy:
            date = pd.to_datetime('today').strftime('%Y-12-31')
            flatten_all_people_eoy = await self.fetch_teams_and_people_as_of_date(eoy)
            all_people_eoy_df = pd.DataFrame(flatten_all_people_eoy)

            # Merge data and perform cleanup for EOY data
            all_people_eoy_df = self.merge_and_clean_data(all_people_eoy_df)

            # Merge EOY data and drop duplicates
            all_people_concat_df = pd.concat([self.people_df, all_people_eoy_df], ignore_index=True)
            all_people_concat_df.drop_duplicates(subset=['BusinessUnitId', 'EmploymentNumber'], inplace=True)


        # Merge data and perform necessary operations
        len(self.people_df)
        self.people_df = self.merge_and_filter_config_data()

        # Remove ids if not needed
        if not with_ids:
            self.people_df = self.people_df.drop(columns=[
                'PersonId', 'BusinessUnitId', 'SiteId', 'TeamId', 'ContractId', 'WorkflowControlSetId', 'ContractId',
                'ContractScheduleId', 'BudgetGroupId', 'PartTimePercentageId', 'ShiftBagId'])

        # Convert to dict if as_df is False
        if not as_df:
            all_people_dict = self.people_df.to_dict(orient='records')
            self.people = all_people_dict
            return all_people_dict

        return self.people_df

    def merge_and_clean_data(self, people_df):
        # Concatenate and clean up the data
        people_df = people_df.drop_duplicates(
            subset=['BusinessUnitId', 'EmploymentNumber'])
        self.bus_df['BusinessUnitId'] = self.bus_df['BusinessUnitId'].astype(
            str)  # Convert to string type
        people_df = pd.merge(
            people_df, self.bus_df, on='BusinessUnitId', how='left')
        people_df.rename(columns={'Id': 'PersonId'}, inplace=True)
        return people_df

    def fetch_config_data_as_df(self):
        self.sites_df = pd.concat(self.sites)
        self.sites_df.rename(columns={'Id': 'SiteId', 'Name': 'SiteName'}, inplace=True)

        self.teams_df = pd.concat(self.teams)
        self.teams_df.rename(columns={'Id': 'TeamId', 'Name': 'TeamName'}, inplace=True)

        self.contracts_df = pd.concat(self.contracts)
        self.contracts_df.rename(columns={'Id': 'ContractId', 'Name': 'ContractName'}, inplace=True)

        self.absences_df = pd.concat(self.absences)
        self.absences_df.rename(columns={'Id': 'AbsenceId', 'Name': 'AbsenceName'}, inplace=True)

        self.roles_df = pd.concat(self.roles)
        self.roles_df.rename(columns={'Id': 'RoleId', 'Name': 'RoleName'}, inplace=True)

        self.contract_schedules_df = pd.concat(self.contract_schedules)
        self.contract_schedules_df.rename(columns={'Id': 'ContractScheduleId', 'Name': 'ContractScheduleName'}, inplace=True)

        self.workflow_control_sets_df = pd.concat(self.workflow_control_sets)
        self.workflow_control_sets_df.rename(columns={'Id': 'WorkflowControlSetId', 'Name': 'WorkflowControlSetName'}, inplace=True)

        self.part_time_percentages_df = pd.concat(self.part_time_percentages)
        self.part_time_percentages_df.rename(columns={'Id': 'PartTimePercentageId', 'Name': 'PartTimePercentageName'}, inplace=True)

        self.shift_bags_df = pd.concat(self.shift_bags)
        self.shift_bags_df.rename(columns={'Id': 'ShiftBagId', 'Name': 'ShiftBagName'}, inplace=True)

        self.budget_groups_df = pd.concat(self.budget_groups)
        self.budget_groups_df.rename(columns={'Id': 'BudgetGroupId', 'Name': 'BudgetGroupName'}, inplace=True)

        self.shift_categories_df = pd.concat(self.shift_categories)
        self.shift_categories_df.rename(columns={'Id': 'ShiftCategoryId', 'Name': 'ShiftCategoryName'}, inplace=True)

        self.scenarios_df = pd.concat(self.scenarios)
        self.scenarios_df.rename(columns={'Id': 'ScenarioId', 'Name': 'ScenarioName'}, inplace=True)

    def fetch_config_data_for_business_unit(self, bu_name):
        self.fetch_config(self.sites, 'sites', bu_name)
        self.fetch_config(self.teams, 'teams', bu_name)
        self.fetch_config(self.absences, 'absences', bu_name)
        self.fetch_config(self.contracts, 'contracts', bu_name)
        self.fetch_config(self.roles, 'roles', bu_name)
        self.fetch_config(self.contract_schedules, 'contract_schedules', bu_name)
        self.fetch_config(self.workflow_control_sets, 'workflow_control_sets', bu_name)
        self.fetch_config(self.part_time_percentages, 'part_time_percentages', bu_name)
        self.fetch_config(self.shift_bags, 'shift_bags', bu_name)
        self.fetch_config(self.budget_groups, 'budget_groups', bu_name)
        self.fetch_config(self.shift_categories, 'shift_categories', bu_name)
        self.fetch_config(self.scenarios, 'scenarios', bu_name)


    def fetch_config(self, data_list, key, bu_name):
        data_to_add = pd.DataFrame(self.config_data[bu_name][key]['Result'])
        data_to_add['BusinessUnitName'] = bu_name
        data_list.append(data_to_add)

    def merge_and_filter_config_data(self):
        self.people_df['BusinessUnitName'] = self.people_df['BusinessUnitName'].astype(str)
        self.people_df['RoleId'] = self.people_df['Roles'].apply(lambda x: self.get_first_role_id(x))
        
        tmp_df = self.people_df.merge(
            self.sites_df, on=['SiteId', 'BusinessUnitName'], how='left')
        tmp_df = tmp_df.merge(self.teams_df, on=[
                              'TeamId', 'SiteId', 'SiteName', 'BusinessUnitName'], how='left')
        tmp_df = tmp_df.merge(self.contracts_df, on=[
                              'ContractId', 'BusinessUnitName'], how='left')
        tmp_df = tmp_df.merge(
            self.roles_df, on=['RoleId', 'BusinessUnitName'], how='left')
        self.people_df = tmp_df

        return self.people_df

    def get_first_role_id(self, role_list):
        if len(role_list) > 0:
            return role_list[0]['RoleId']
        else:
            return None

    def add_people_by_df(self, people_df):
        log = []
        # merge config data to get the ids
        people_df = people_df.merge(self.teams_df, on=['TeamName', 'BusinessUnitName'], how='left') if 'TeamId' not in people_df.columns else people_df
        people_df = people_df.merge(self.contracts_df, on=['ContractName', 'BusinessUnitName'], how='left') if 'ContractId' not in people_df.columns else people_df
        people_df = people_df.merge(self.roles_df, on=['RoleName', 'BusinessUnitName'], how='left') if 'RoleId' not in people_df.columns else people_df
        people_df = people_df.merge(self.bus_df, on=['BusinessUnitName'], how='left') if 'BusinessUnitId' not in people_df.columns else people_df
        people_df = people_df.merge(self.contract_schedules_df, on=['ContractScheduleName','BusinessUnitName'], how='left') if 'ContractScheduleId' not in people_df.columns else people_df
        people_df = people_df.merge(self.workflow_control_sets_df, on=['WorkflowControlSetName','BusinessUnitName'], how='left') if 'WorkflowControlSetId' not in people_df.columns else people_df
        people_df = people_df.merge(self.part_time_percentages_df, on=['PartTimePercentageName','BusinessUnitName'], how='left') if 'PartTimePercentageId' not in people_df.columns else people_df
        people_df = people_df.merge(self.shift_bags_df, on=['ShiftBagName','BusinessUnitName'], how='left') if 'ShiftBagId' not in people_df.columns else people_df
        people_df = people_df.merge(self.budget_groups_df, on=['BudgetGroupName','BusinessUnitName'], how='left') if 'BudgetGroupId' not in people_df.columns else people_df
        people_df = people_df.merge(self.shift_categories_df, on=['ShiftCategoryName','BusinessUnitName'], how='left') if 'ShiftCategoryId' not in people_df.columns else people_df
        people_df = people_df.merge(self.scenarios_df, on=['ScenarioName','BusinessUnitName'], how='left') if 'ScenarioId' not in people_df.columns else people_df

        for person in people_df.to_dict(orient='records'):
            person_request = self.client.AddPersonRequest(
                TimeZoneId = person['TimeZoneId'],
                BusinessUnitId = person['BusinessUnitId'],
                FirstName = person['FirstName'],
                LastName = person['LastName'],
                StartDate = person['StartDate'],
                Email = person['Email'],
                EmploymentNumber = person['EmploymentNumber'],
                ApplicationLogon = person['ApplicationLogon'],
                Identity = person['Identity'],
                TeamId = person['TeamId'],
                ContractId = person['ContractId'],
                ContractScheduleId = person['ContractScheduleId'],
                PartTimePercentageId = person['PartTimePercentageId'],
                RoleIds = [person['RoleId']],
                WorkflowControlSetId = person['WorkflowControlSetId'],
                ShiftBagId = person['ShiftBagId'] if 'ShiftBagId' in person else None,
                BudgetGroupId = person['BudgetGroupId'] if 'BudgetGroupId' in person else None,
                FirstDayOfWeek = person['FirstDayOfWeek'] if 'FirstDayOfWeek' in person else None,
                Culture = person['Culture'] if 'Culture' in person else None,
            )
            res = self.client.add_person(person_request)
            log.append(res)
        
        return log


class PersonAccountsManager:
    '''
    This class is used to fetch the person accounts data from the API and merge it with the config data.
    '''
    def __init__(self, client, people_df=None, config_data=None):
        self.client = client
        self.people_df = people_df
        self.config_data = config_data

    async def fetch_config_data(self, exclude_bu_names=[]):
        if not hasattr(self, 'config_data'):
            self.config_manager = ConfigManager(self.client)
            if self.client.set_async:
                self.config_data = await self.config_manager.create_config_from_api(exclude_bu_names=exclude_bu_names)
            else:
                self.config_data = await self.config_manager.create_config_from_api(exclude_bu_names=exclude_bu_names)

    def fetch_config(self, data_list, key, bu_name):
        data_to_add = pd.DataFrame(self.config_data[bu_name][key]['Result'])
        data_to_add['BusinessUnitName'] = bu_name
        data_list.append(data_to_add)

    async def fetch_config_data_as_df(self, exclude_bu_names=[]):
        await self.fetch_config_data(exclude_bu_names=exclude_bu_names)
        self.absences = []
        [self.fetch_config(self.absences, 'absences', bu['Name'])
         for bu in self.config_data['bus']]
        self.absences_df = pd.concat(self.absences)
        self.absences_df.rename(
            columns={'Id': 'AbsenceId', 'Name': 'AbsenceName'}, inplace=True)

    async def fetch_person_accounts(self, date=None, people_df=None, client=None, with_id=False, details=False):
        if people_df is None:
            people_df = self.people_df
        if client is None:
            client = self.client
        # if date is None, then today
        if date is None:
            date = pd.to_datetime('today').strftime('%Y-%m-%d')

        person_accounts_with_id = []
        for index, person_tuple in people_df.iterrows():
            person_id = person_tuple['PersonId']
            person_accounts = await client.get_person_accounts_by_person_id(person_tuple['BusinessUnitId'], person_id, date)
            person_accounts_result = person_accounts['Result']
            for account in person_accounts_result:
                account_with_person_id = {'PersonId': person_id, **account}
                person_accounts_with_id.append(account_with_person_id)

        # flatten person_accounts
        # flattened_person_accounts = [account for accounts in person_accounts_with_id for account in accounts]
        # print(flattened_person_accounts)
        person_accounts_df = pd.DataFrame(person_accounts_with_id)

        # using people_df, add peoples' email and employment number to person_accounts on person_id
        person_accounts_df = person_accounts_df.merge(
            people_df[['BusinessUnitName', 'PersonId', 'Email', 'EmploymentNumber', 'ContractName']], on='PersonId', how='left')
        # load_config if absences_df is not defined
        if not hasattr(self, 'absences_df'):
            await self.fetch_config_data()
            await self.fetch_config_data_as_df()

        # merge with absences_df
        person_accounts_df = person_accounts_df.merge(
            self.absences_df, on=['AbsenceId', 'BusinessUnitName'], how='left')
        person_accounts_df['StartDate'] = pd.to_datetime(
            person_accounts_df['Period'].apply(lambda x: x['StartDate']))
        person_accounts_df['EndDate'] = pd.to_datetime(
            person_accounts_df['Period'].apply(lambda x: x['EndDate']))
        person_accounts_df = person_accounts_df.drop(columns=['Period'])

        if not with_id:
            person_accounts_df = person_accounts_df.drop(
                columns=['PersonId', 'AbsenceId'])

        if not details:
            person_accounts_df = person_accounts_df.drop(columns=['Priority', 'Requestable', 'InWorkTime', 'InPaidTime', 'PayrollCode',
                                                                  'Confidential', 'InContractTime', 'TrackerType', 'IsDeleted'])

        self.person_accounts_df = person_accounts_df

        return person_accounts_df

    async def add_or_update_person_accounts_by_df(self, person_accounts_df=None, people_df=None, client=None, by_df=True):
        if client is None:
            client = self.client

        if person_accounts_df is None:
            person_accounts_df = self.person_accounts_df

        if people_df is None:
            people_df = self.people_df

        person_accounts = person_accounts_df.to_dict(orient='records')

        # add PersonId and AbsenceId using people_df and self.absence_df if not present
        if 'PersonId' not in person_accounts[0].keys() or 'AbsenceId' not in person_accounts[0].keys():
            person_accounts = [self.add_person_id_and_absence_id(
                account, people_df) for account in person_accounts]

        # convert StartDate and EndDate to string
        person_accounts = [self.convert_date_to_string(
            account) for account in person_accounts]

        person_accounts = await asyncio.gather(
            *[client.add_or_update_person_account_for_person(person_account['PersonId'], person_account['AbsenceId'], person_account['StartDate'], person_account['BalanceIn'], person_account['Extra'], person_account['Accrued']) for person_account in person_accounts]
        )
        return person_accounts

    def add_person_id_and_absence_id(self, account, people_df):
        person_id = people_df[(people_df['BusinessUnitName'] == account['BusinessUnitName']) & (
            people_df['EmploymentNumber'] == account['EmploymentNumber'])]['PersonId'].tolist()[0]
        absence_id = self.absences_df[(self.absences_df['BusinessUnitName'] == account['BusinessUnitName']) & (
            self.absences_df['AbsenceName'] == account['AbsenceName'])]['AbsenceId'].tolist()[0]
        account['PersonId'] = person_id
        account['AbsenceId'] = absence_id
        return account

    def convert_date_to_string(self, account):
        account['StartDate'] = account['StartDate'].strftime('%Y-%m-%d')
        account['EndDate'] = account['EndDate'].strftime('%Y-%m-%d')
        return account
