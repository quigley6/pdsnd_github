import cmd, datetime, sys, os, re
import pandas as pd

CITIES = [
    'washington',
    'new york',
    'chicago'
]

MONTHS = [
    'all',
    'january',
    'february',
    'march',
    'april',
    'may',
    'june',
    'july',
    'august',
    'september',
    'october',
    'november',
    'december'
]

MONTH_IDX = {
    0: 'all',
    1: 'january',
    2: 'february',
    3: 'march',
    4: 'april',
    5: 'may',
    6: 'june',
    7: 'july',
    8: 'august',
    9: 'september',
    10: 'october',
    11: 'november',
    12: 'december'
}

WEEKDAYS = {
    0: 'Sunday',
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday'
}

class BikeShare(cmd.Cmd):
    intro = '\n{0}\nWelcome! Let\'s explore some bike share data!\n\nType \'help\' or <tab><tab> to list commands\n{0}\n'.format('-' * 50)
    prompt = '<select city with \'city\' command>$ '

    city_data = None
    city_name = 'none'

    filter_month = 'all'

    def do_popular_times(self, arg):
        """\nDisplay statistics for most popular month, weekday, and hour to start a trip.\n\nResults are filtered by the \'month\' command"""
        if self.city_data is None:
            self.output('You\'ll need to select a city first')
            return

        #filter to month, if set
        work_set = self.month_filter(self.city_data)
        if len(work_set) <= 0:
            self.output('Whoops! That city has no data for the specified month, please choose another!')
            return

        #most popular month
        pop_month = ''
        if self.filter_month != 'all':
            pop_month = self.filter_month
            month_high = 'all'
        else:
            month_counts = work_set.resample('M')['Trip Duration'].count()
            month_high = month_counts.max()
            pop_month = MONTH_IDX[month_counts[month_counts == month_high].index[0].month]

        #most popular weekday
        weekday_counts = work_set.groupby(['Weekday'])['Trip Duration'].count()
        weekday_high = weekday_counts.max()
        pop_weekday = WEEKDAYS[weekday_counts[weekday_counts == weekday_high].index[0]]

        #most popular hour
        hour_counts = work_set.resample('H')['Trip Duration'].count()
        hour_high = hour_counts.max()
        pop_hour = hour_counts[hour_counts == hour_high].index[0].hour

        self.output("""
Popular Trip Starts for {0} in the month of {1}:
The most popular month is: {2} ({3} trips)
The most popular weekday is: {4} ({5} trips)
The most popular hour is: {6}:00 ({7} trips)
        """.format(self.city_name, self.filter_month, pop_month, month_high, pop_weekday, weekday_high, pop_hour, hour_high))

    def do_popular_stations(self, arg):
        """\nDisplay statistics for station popularity\n"""
        if self.city_data is None:
            self.output('You\'ll need to select a city first')
            return

        #filter to month, if set
        work_set = self.month_filter(self.city_data)
        if len(work_set) <= 0:
            self.output('Whoops! That city has no data for the specified month, please choose another!')
            return

        # most popular start station
        start_counts = work_set.groupby(['Start Station'])['Trip Duration'].count()
        start_high = start_counts.max()
        pop_start = start_counts[start_counts == start_high].index[0]

        #most popular end station
        end_counts = work_set.groupby(['End Station'])['Trip Duration'].count()
        end_high = end_counts.max()
        pop_end = end_counts[end_counts == end_high].index[0]

        #most popular station combo
        trip_counts = work_set.groupby(['Start Station', 'End Station'])['Trip Duration'].count()
        trip_high = trip_counts.max()
        pop_trip = trip_counts[trip_counts == trip_high].index[0]

        self.output("""
Popular Stations for {0} in the month of {1}:
The most popular starting station is: {2} ({3} trips)
The most popular ending station is: {4} ({5} trips)
The most popular trip begins at {6}, and ends at {7} ({8} trips)
        """.format(self.city_name, self.filter_month, pop_start, start_high, pop_end, end_high, pop_trip[0], pop_trip[1], trip_high))

    def do_travel_time(self, arg):
        """\nDisplay travel time statistics\n"""
        if self.city_data is None:
            self.output('You\'ll need to select a city first')
            return

        #filter to month, if set
        work_set = self.month_filter(self.city_data)
        if len(work_set) <= 0:
            self.output('Whoops! That city has no data for the specified month, please choose another!')
            return

        #total travel time
        total_seconds = work_set['Trip Duration'].sum()
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        total_time = '{} years, {} days, {} hours, {} minutes, {} seconds'.format(int(y), int(d), int(h), int(m), int(s))

        #average travel time
        mean_seconds = int(work_set['Trip Duration'].mean()) # truncate microseconds
        mean_time = datetime.timedelta(seconds=mean_seconds)

        self.output("""
Travel time statistics in {0} for the month of {1}:
Total trip time: {2} seconds ({3})
Average trip duration: {4} seconds ({5}) """.format(self.city_name, self.filter_month, total_seconds, total_time, mean_seconds, mean_time))

    def do_user_info(self, arg):
        """\nDisplay user statistics\n"""
        if self.city_data is None:
            self.output('You\'ll need to select a city first')
            return

        #filter to month, if set
        work_set = self.month_filter(self.city_data)
        if len(work_set) <= 0:
            self.output('Whoops! That city has no data for the specified month, please choose another!')
            return

        #user type
        user_counts = work_set.groupby(['User Type'])['Trip Duration'].count()
        user_type_display = '\n    '.join('{}: {}'.format(x, user_counts[x]) for x in user_counts.index)

        #gender info
        try:
            gender_counts = work_set.groupby(['Gender'])['Trip Duration'].count()
            gender_display = '\n    '.join('{}: {}'.format(x, gender_counts[x]) for x in gender_counts.index)

        except KeyError:
            gender_display = 'Gender data not available'

        #birth year
        try:
            birth_counts = work_set.groupby(['Birth Year'])['Trip Duration'].count()
            birth_high = birth_counts.max()
            common_birth = int(birth_counts[birth_counts == birth_high].index[0])

            earliest_birth = int(work_set['Birth Year'].min())
            latest_birth = int(work_set['Birth Year'].max())

            now = datetime.datetime.now()

            birth_display = 'Oldest customer: {0} (born {1})\n    Youngest customer: {2} (born {3})\n    Most common customer: {4} (born {5})'.format( \
                now.year - earliest_birth, earliest_birth, now.year - latest_birth, latest_birth, now.year - common_birth, common_birth)
        
        except KeyError:
            birth_display = 'Age data not available'

        self.output("""
User statistics in {0} for the month of {1}:
User Types:
    {2}
Gender:
    {3}
Age:
    {4}""".format(self.city_name, self.filter_month, user_type_display, gender_display, birth_display))

    def do_month(self, arg):
        """\nSpecify a month to limit statistics to. Double-tab for options\n"""
        if arg in MONTHS:
            self.filter_month = arg
        else:
            self.output('Sorry, I don\'t recognize the month of \'{}\''.format(arg))

    def complete_month(self, text, line, begidx, endidx):
        """Creates tab-completion data for the city command"""
        if not text:
            completions = MONTHS[:]
        else:
            completions = [x for x in MONTHS if x.startswith(text)]

        return completions

    def do_city(self, arg):
        """\nSelect the city for which to view bike share data. Options are:
* 'washington': Washington D.C.
* 'new york': New York, NY
* 'chicago': Chicago, IL\n"""

        city = arg.lower()
        if re.match('[Nn]ew [Yy]ork.*', city):
            self.city_data = pd.read_csv('new_york_city.csv', index_col='Start Time', parse_dates=['Start Time', 'End Time'], infer_datetime_format=True)
            self.prompt = 'New York>$ '
            self.city_name = 'New York'
        elif re.match('[Ww]ashington.*', city):
            self.city_data = pd.read_csv('washington.csv', index_col='Start Time', parse_dates=['Start Time', 'End Time'], infer_datetime_format=True)
            self.prompt = 'Washington D.C.>$ '
            self.city_name = 'Washington D.C.'
        elif re.match('[Cc]hicago.*', city):
            self.city_data = pd.read_csv('chicago.csv', index_col='Start Time', parse_dates=['Start Time', 'End Time'], infer_datetime_format=True)
            self.prompt = 'Chicago>$ '
            self.city_name = 'Chicago'
        else:
            self.output('Sorry, I don\'t have data for {}, please try again'.format(arg))

        if self.city_data is not None:
            # add a weekday column for each Start Time
            self.city_data['Weekday'] = self.city_data.index.weekday

    def do_raw_data(self, arg):
        """\nDisplay raw city data, filtered by month\n"""
        if self.city_data is None:
            self.output('You\'ll need to select a city first')
            return

        #filter to month, if set
        work_set = self.month_filter(self.city_data)
        if len(work_set) <= 0:
            self.output('Whoops! That city has no data for the specified month, please choose another!')
            return

        idx = 0
        stop = False
        while not stop:
            print(work_set[idx:idx+5])

            answer = input('\n\nPrint more? [yes/NO]:')
            if re.match('[Nn][Oo]', answer) or len(answer) <= 0: # no is default
                stop = True
            else:
                idx += 5

    def complete_city(self, text, line, begidx, endidx):
        """Creates tab-completion data for the city command"""
        if not text:
            completions = CITIES[:]
        else:
            completions = [x for x in CITIES if x.startswith(text)]

        return completions

    def do_config(self, arg):
        """Print the current city and filter configuration"""
        self.output('Current configuration:\n* Month: {}\n* City: {}'.format(self.filter_month, self.city_name))

    def do_clear(self, arg):
        """\nClears the screen\n"""
        self.clear()

    def do_quit(self, arg):
        """\nExits the program\n"""
        self.close()

    def do_bye(self, arg):
        """\nExits the program\n"""
        self.close()

    def month_filter(self, df):
        if self.filter_month != 'all':
            filter_string = '{} 2017'.format(self.filter_month)
            retset = df.loc[filter_string]
        else:
            retset = df.copy()

        return retset

    def output(self, message):
        """Print a nicely formatted message"""
        print('\n{0}\n{1}\n{0}\n'.format('-' * 50, message))

    def clear(self):
        """Clear the screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def close(self):
        """Cleanly close and exit"""
        self.output('Thanks for using BikeShare! Bye!')
        sys.exit(0)

if __name__ == '__main__':
    try:
        BikeShare().cmdloop()
    except KeyboardInterrupt:
        print('\n\nThanks for using BikeShare! Bye!\n\n')
        sys.exit(0)