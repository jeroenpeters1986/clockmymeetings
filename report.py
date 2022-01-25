import datetime
import os
import time
from clockify_api_client.client import ClockifyAPIClient
from dotenv import load_dotenv

load_dotenv()


def get_work_week_span():
    """ Get the start- and enddate from the current workweek as a string"""

    now = datetime.date.today()
    start_of_current_week = now - datetime.timedelta(days=now.weekday())
    end_of_work_week = start_of_current_week + datetime.timedelta(days=4)

    return (start_of_current_week.strftime('%Y-%m-%dT00:00:00.001Z'),
            end_of_work_week.strftime('%Y-%m-%dT23:59:59.001Z'))


def clockify_time_to_object(time_string):
    """ Convert the Clockify string (PT1H30M, PT1H, PT30M) to a time object """
    time_format = '%I:%M'

    if "H" in time_string and "M" not in time_string:
        time_format = '%I:'

    if "H" not in time_string and "M" in time_string:
        time_format = '%M'

    ftime = time_string.replace("PT", "").replace("M", "").replace("H", ":")

    return time.strptime(ftime, time_format)


def seconds_to_hours(seconds):
    """ Convert seconds to hours """
    return datetime.timedelta(seconds=seconds)


CLOCKIFY_API_URL = 'api.clockify.me/v1'
CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')

client = ClockifyAPIClient().build(CLOCKIFY_API_KEY, CLOCKIFY_API_URL)
workweek = get_work_week_span()

print("       Tijdsperiode", workweek[0][:10], "-", workweek[1][:10])
print("     ========================================\n")

workspace_id = client.workspaces.get_workspaces()[0]['id']
current_user = client.users.get_current_user()

tags = client.tags.get_tags(workspace_id)
meeting_tag_id = ''
for tag in tags:
    if tag['name'] == 'Meetings':
        meeting_tag_id = tag['id']

entries = client.time_entries.get_time_entries(
    workspace_id,
    current_user['id'],
    {'start': workweek[0], 'end': workweek[1]})

total_seconds = 0
meeting_seconds = 0
for entry in entries:
    if not entry['timeInterval']['duration']:
        continue

    time_spent = clockify_time_to_object(entry['timeInterval']['duration'])
    total_entry_seconds = (time_spent.tm_hour*60*60) + (time_spent.tm_min*60)

    for tag_id in entry['tagIds']:
        if tag_id == meeting_tag_id:
            print("  MEETING :  ", entry['description'],
                  seconds_to_hours(total_entry_seconds))
            meeting_seconds += total_entry_seconds

    total_seconds += total_entry_seconds

print("\n===============================================")
print("Totale tijd geregistreerd:              {}".format(
    seconds_to_hours(total_seconds)))
print("Totale tijd in meeting:                 {}".format(
    seconds_to_hours(meeting_seconds)))
print("Percentage tijd getagd met 'Meeting':   {:.2f}%".format(
    100/total_seconds * meeting_seconds))

