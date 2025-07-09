from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
import calendar
from calendar import HTMLCalendar #imported again since calendar.HTMLCalendar wont work, so this way I can use HTMLCalendar
from django.core.mail import send_mail
import datetime
import requests
import pytz
from math import ceil


from .models import User, Club, Drill, Event, Calendar

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        current_datetime = datetime.datetime.now(pytz.timezone(request.user.time_zone))
        next_week_datetime = current_datetime.date() + datetime.timedelta(days=7)
        current_day = current_datetime.day
        current_month = current_datetime.month
        current_year = current_datetime.year
        items = schedule_page_items(request, current_month, current_year)
        months_calendar = items[0]

        first_day = current_datetime.replace(day=1)
        adjusted_day = current_day + first_day.weekday()
        current_week_of_month = int(ceil(adjusted_day/7))
        next_week_of_month = current_week_of_month + 1
        num_weeks = len(calendar.monthcalendar(current_year,current_month))

        if current_week_of_month == num_weeks:
            next_week_of_month = 1
        
        header_rows = months_calendar.split('<tr>')[:3]
        month_row = header_rows[1]
        days_row = header_rows[2]
        weeks = months_calendar.split('<tr>')[2:] #ignoring top header rows
        current_week_html = '<tr>' + month_row + '<tr>' + days_row + '<tr>' + weeks[current_week_of_month]
        next_week_html = ""

        if next_week_of_month != 1:
            current_week_html += '<tr>' + weeks[next_week_of_month]
        else:
            next_month = next_week_datetime.month
            next_year = next_week_datetime.year
            next_items = schedule_page_items(request, next_month, next_year)
            next_months_calendar = next_items[0]
            header_rows = next_months_calendar.split('<tr>')[:3]
            month_row = header_rows[1]
            days_row = header_rows[2]
            weeks = next_months_calendar.split('<tr>')[2:] #ignoring top header rows
            next_week_html = '<tr>' + month_row + '<tr>' + days_row + '<tr>' + weeks[1]
    else:
        current_week_html = ""
        next_week_html = ""

    return render(request, 'training/index.html', {
        "week_calendar": current_week_html,
        "next_week_calendar": next_week_html,
    })

def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "training/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "training/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    competitions = get_competitions()
    teams = None
    selected_competition = None

    if request.method == "POST":
        # if i am submitting the competition form
        if 'competition_id' in request.POST:
            competition_id = request.POST['competition_id']
            selected_competition = next((comp for comp in competitions if str(comp['id']) == competition_id), None)
            teams = get_teams(competition_id)
            return render(request, "training/register.html", {
                'competitions': competitions,
                'selected_competition': selected_competition,
                'teams': teams,
            })
        elif 'team_of_user' in request.POST:
            competition_id = request.POST['competition_id_in_teamForm']
            selected_competition = next((comp for comp in competitions if str(comp['id']) == competition_id), None)
            teams = get_teams(competition_id)

            info = request.POST['team_of_user'].split(',')
            team_name = info[0]
            team_id = info[1]
            selected_team = None
            for team in teams:
                if str(team['name']) == str(team_name):
                    selected_team = team

            persons = get_coach_and_squad(team_id)
            coach = persons[0]
            squad = persons[1]

            return render(request, "training/register.html", {
                'competitions': competitions,
                'selected_competition': selected_competition,
                'teams': teams,
                'selected_team': selected_team,
                'coach': coach,
                'squad': squad,
            })

        else:
            username = request.POST["username"]
            email = request.POST["email"]
            player_id = request.POST['player']
            coach_id = request.POST['coach']
            if player_id != "none":
                person = get_person(player_id)
            else:
                person = get_person(coach_id)
            name = person['name'].split(" ", 1)
            first_name = name[0]
            last_name = name[1]
            date_of_birth = person['dateOfBirth']
            nationality = person['nationality']
            person_api_id = person['id']
            is_coach = request.POST["is_coach"] == 'True'
            club_info = request.POST["club"].split(',')
            club_name = club_info[0]
            club_api_id = club_info[1]
            try:
                club_object = Club.objects.get(name=club_name, club_api_id = club_api_id)

            except Club.DoesNotExist:
                club_object = Club.objects.create(name=club_name, coach=None, club_api_id = club_api_id)
                club_object.save()
                calendar = Calendar.objects.create(club = club_object)
                calendar.save()            
            
            timezone = request.POST['user_time_zone']
            list_of_api_ids = User.objects.all().values_list('api_id', flat=True)

            if (int(person_api_id) in list_of_api_ids):
                players_account = User.objects.get(club = club_object, api_id = person_api_id)
                if players_account and not players_account.is_coach:
                    return render(request, "training/register.html", {
                        "message": "This player already has an account with this club",
                        'competitions': competitions,
                        'selected_competition': selected_competition,
                        'teams': teams,

                    })


 

            # Ensure password matches confirmation
            password = request.POST["password"]
            confirmation = request.POST["confirmation"]
            if password != confirmation:
                return render(request, "training/register.html", {
                    "message": "Passwords must match.",
                    'competitions': competitions,
                    'selected_competition': selected_competition,
                    'teams': teams,

                })

            # Attempt to create new user
            try:
                user = User.objects.create_user(username, email, password)
                user.first_name = first_name
                user.last_name = last_name
                user.is_coach = is_coach
                user.time_zone = timezone
                user.DoB = date_of_birth
                user.nationality = nationality
                user.api_id = person_api_id
                user.save()
                if user.is_coach:
                    club_object.coach = user
            
            except IntegrityError:
                return render(request, "training/register.html", {
                    "message": "Username already taken.",
                    'competitions': competitions,
                    'selected_competition': selected_competition,
                    'teams': teams,
                })
                
            # Check if club already exists
            try:
                club = Club.objects.get(name=club_name, club_api_id = club_api_id)
                if is_coach:
                    if club.coach is None:
                        club.coach = user
                        club.save()
                        user.club = club
                        user.save()
                    else:
                        User.objects.filter(username = user.username).delete()
                        return render(request, "training/register.html", {
                            "message": "The coach of this club already has an account.",
                            'competitions': competitions,
                            'selected_competition': selected_competition,
                            'teams': teams,
                        })
                else:
                    user.club = club
                    user.save()
                    
            except Club.DoesNotExist:
                club = Club.objects.create(name=club_name, coach=user if is_coach else None, club_api_id = club_api_id)
                club.save()
                calendar = Calendar.objects.create(club = club)
                calendar.save()
                user.club = club
                user.save()
                    
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
    
    return render(request, "training/register.html", {
        'competitions': competitions,
        'teams': teams,
        'selected_competition': selected_competition
    })

@login_required
def drill_library(request, message=None):
    drills = Drill.objects.filter(coach = request.user)
    return render(request, 'training/drills.html', {
        "drills": drills,
        "message": message
    })

@login_required
def create_drill(request):
    if request.method == "POST":
        drills = Drill.objects.filter(coach = request.user)
        if request.user.is_coach:
            drill_name = request.POST["drill_name"]
            description = request.POST["description"]
            coach = request.user
            drill_video = request.POST["drill_video"]
            if drill_name == "" or description == "":
                return render(request, 'training/drills.html', {
                    "drills": drills,
                    "message": "You cannot leave these fields blank."
                })
            drill = Drill.objects.create(name = drill_name, description = description, coach = coach, video_url = drill_video)
            drill.save()
        else:
            return render(request, 'training/drills.html', {
                "message": "You cannot add a drill as you are not a coach."
            })
    return HttpResponseRedirect(reverse('drill_library'))

def drill_view(request, drill_id):
    if len(Drill.objects.filter(pk=drill_id)) == 0:
        return render(request, 'training/drill.html', {
            "message": "This drill does not exist",
        })
    drill = Drill.objects.get(pk=drill_id)
    if (drill.coach == request.user) or (drill.coach.club == request.user.club): # if the user trying to access the drills is the coach or a player of the coach
        return render(request, 'training/drill.html', {
            "drill": drill,
        })
    else:
        return render(request, 'training/drill.html', {
            "message": "You do not have permission to view this drill"
        })
    
@login_required
def schedule(request, month_num, year, message=None):
    items = schedule_page_items(request, month_num, year)
    cal = items[0]
    users_calendar = items[1]
    drills_of_coach = items[2]

    return render(request, "training/schedule.html", {
        "cal": cal,
        "users_calendar": users_calendar,
        "drills_of_coach": drills_of_coach,
        "message": message

    })

@login_required
def add_event(request):
    if request.method == 'POST':
        calendar_of_user = Calendar.objects.get(club = request.user.club)
        title = request.POST['title']
        drill_ids = request.POST.getlist('drills')
        event_type = request.POST['event_type']
        date_time_str = request.POST['date_time']
        try:
            date_time = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        except:
            dt = datetime.datetime.now()
            message = "You must fill in all fields correctly"
            return schedule(request, dt.month, dt.year, message)
        local = pytz.timezone("Asia/Dubai")
        naive = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        description = request.POST['description']
        new_event = Event(
            calendar = calendar_of_user,
            title = title,
            event_type = event_type,
            date_time = utc_dt,
            description = description
        )
        
        new_event.save()
        
        new_event.drills.set(Drill.objects.filter(id__in=drill_ids))


    month_num = datetime.datetime.now().month
    year = datetime.datetime.now().year

    return HttpResponseRedirect(reverse(schedule, kwargs={
        "month_num": month_num, "year": year
    }))
            
@login_required
def delete_event(request, event_id, day, month, year):
    if request.method == "POST":
        clubOfUser = request.user.club
        calendarOfUser = Calendar.objects.get(club=clubOfUser)
        if request.user.is_coach:
            try:
                event_to_delete = Event.objects.get(pk=event_id, calendar=calendarOfUser)
                event_to_delete.delete()
                return JsonResponse({'status': 'success'})
            except Event.DoesNotExist:
                return JsonResponse({'status': 'fail', 'reason': 'Event does not exist'}, status=404)
        return JsonResponse({'status': 'fail', 'reason': 'Permission denied'}, status=403)
    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def delete_drill(request, drill_id):
    message = None
    if request.method == "POST":
        if request.user.is_coach:
            try:
                drill_to_delete = Drill.objects.get(pk=drill_id, coach=request.user)
                drill_to_delete.delete()
                return drill_library(request)
            except Drill.DoesNotExist:
                message = "You cannot delete this drill as it does not belong to you or does not exist"
        else:
            message = "You cannot delete this as you are not a coach"
        return drill_library(request, message)
    return HttpResponseRedirect(reverse('drill_library'))

@login_required
def day_details(request, day, month, year):
    clubOfUser = request.user.club
    calendarOfUser = Calendar.objects.get(club = clubOfUser)
    user_timezone = request.user.time_zone
    month_name = list(calendar.month_name)[month]
    matchday = False

    dt = datetime.datetime(year, month, day)

    old_timezone = pytz.timezone(user_timezone)
    new_timezone = pytz.timezone("UTC")

    localized_datetime = old_timezone.localize(dt)
    start_datetime = localized_datetime.astimezone(new_timezone)
    end_datetime = start_datetime + datetime.timedelta(days=1)
    events = (Event.objects.filter(date_time__range=(start_datetime,end_datetime) ,calendar = calendarOfUser) | Event.objects.filter(date_time__range=(start_datetime,end_datetime) ,calendar2 = calendarOfUser) ).order_by('date_time')
    eventsWithLocalTimes = [(event, event.date_time.astimezone(pytz.timezone(user_timezone))) for event in events]


    
    for event in events:
        if event.match_id != None:
            matchday = True
            status = event.status
            match_id = event.match_id

    if matchday and status != "FINISHED":
        match = get_match_by_id(match_id)
        Update_or_Add_match(request, match)

    events = (Event.objects.filter(date_time__range=(start_datetime,end_datetime) ,calendar = calendarOfUser) | Event.objects.filter(date_time__range=(start_datetime,end_datetime) ,calendar2 = calendarOfUser) ).order_by('date_time')
    eventsWithLocalTimes = [(event, event.date_time.astimezone(pytz.timezone(user_timezone))) for event in events]



    return render(request, "training/day.html", {
            "events": events,
            "eventsWithLocalTimes": eventsWithLocalTimes,
            "month_num": month,
            "month_name": month_name,
            "day": day,
            "year": year,
            "matchday": matchday,
            "user_timezone": user_timezone
        })

def get_competitions():
    uri = 'http://api.football-data.org/v4/competitions/'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }

    response = requests.get(uri, headers=headers, allow_redirects=False)
    competitions = response.json()['competitions']
    return competitions

def get_teams(competition_id):
    uri = f'http://api.football-data.org/v4/competitions/{competition_id}/teams'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }
    response = requests.get(uri, headers=headers, allow_redirects=False)
    teams = response.json()['teams']
    return teams

def get_coach_and_squad(team_id):
    uri = f'http://api.football-data.org/v4/teams/{team_id}'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }
    response = requests.get(uri, headers=headers, allow_redirects=False)
    coach = response.json()['coach']
    squad = response.json()['squad']
    return coach, squad

def get_matches(team_id):
    year = datetime.datetime.now().year
    uri = f'http://api.football-data.org/v4/teams/{team_id}/matches?season={year-1}'
    uri2 = f'http://api.football-data.org/v4/teams/{team_id}/matches?season={year}'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }
    response = requests.get(uri, headers=headers, allow_redirects=False)
    response2 = requests.get(uri2, headers=headers, allow_redirects=False)
    last_season_games = response.json()['matches']
    this_season_games = response2.json()['matches']
    return last_season_games, this_season_games

def get_match_by_id(match_id):
    uri = f'http://api.football-data.org/v4/matches/{match_id}'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }
    response = requests.get(uri, headers=headers, allow_redirects=False)
    match = response.json()
    return match

def get_person(person_id):
    uri = f'http://api.football-data.org/v4/persons/{person_id}'
    headers = { 'X-Auth-Token': '7fefad79448c4fefabdb4450b898e666' }
    response = requests.get(uri, headers=headers, allow_redirects=False)
    person = response.json()
    return person

@login_required
def schedule_page_items(request, month_num, year):
    clubOfUser = request.user.club
    calendarOfUser = Calendar.objects.get(club = clubOfUser)
    events = (Event.objects.filter(date_time__year=year, date_time__month=month_num, calendar = calendarOfUser) | Event.objects.filter(date_time__year=year, date_time__month=month_num, calendar2 = calendarOfUser)).order_by('date_time')
    cal = HTMLCalendar().formatmonth(year,month_num)
    user_timezone = request.user.time_zone
    if request.user.is_coach:
        drills_of_coach = Drill.objects.filter(coach = request.user)
    else:
        drills_of_coach = None
    for event in events:
        datetime_for_user = event.date_time.astimezone(pytz.timezone(user_timezone))
        href_redirect = reverse('day_details', args=[datetime_for_user.day, datetime_for_user.month, datetime_for_user.year])
        weekday_name = datetime_for_user.strftime('%A').lower()
        class_name = weekday_name[0:3]
        event_html = f'<div class="{event.event_type.lower()}"><a class="{event.event_type.lower()}_day" href={href_redirect}>{datetime_for_user.day}</a></div>'
        day_html = f'<td class="{class_name}">{event_html}</td>'
        cal = cal.replace(f'<td class="{class_name}">{datetime_for_user.day}</td>', day_html)
    return cal, calendarOfUser, drills_of_coach


#update / sync calendar with real matches for your team
@login_required
def sync_calendar(request, team_id):
    team_id = int(team_id)
    matches = get_matches(team_id)
    last_season_matches = matches[0]
    print(last_season_matches)
    print(len(last_season_matches))
    this_season_matches = matches[1]
    month_num = datetime.datetime.now().month
    year = datetime.datetime.now().year

    for match in last_season_matches:
        Update_or_Add_match(request, match)
    for match in this_season_matches:
        Update_or_Add_match(request, match)

    return HttpResponseRedirect(reverse(schedule, kwargs={
        "month_num": month_num, "year": year
    }))

@login_required
def Update_or_Add_match(request, match):
    user_club = request.user.club
    user_calendar = Calendar.objects.get(club = user_club)
    match_ids = Event.objects.values_list('match_id', flat=True)
    home_team = match["homeTeam"]
    away_team = match["awayTeam"]
    competition = match["competition"]
    score = match["score"]
    date_time_of_match = match['utcDate']
    international_continents = ['South America', 'Asia', 'Europe', 'Africa', 'Oceania', 'World']
    if match['area']['name'] in international_continents:
        match_type = 'National'
    else:
        match_type = 'Club'

    if match["id"] not in match_ids:
        date_time = datetime.datetime.strptime(date_time_of_match, '%Y-%m-%dT%H:%M:%SZ')

        if home_team["name"] == None:
            home_team["name"] = "TBD"
        if away_team["name"] == None:
            away_team["name"] = "TBD"

        new_match = Event(
            calendar = user_calendar,
            event_type = 'Match',
            title = f"{home_team['name']} vs {away_team['name']}",
            date_time = date_time,
            match_id = match["id"],
            match_type = match_type,
            match_competition = competition["name"],
            competition_emblem = competition["emblem"],
            match_matchday = match["matchday"],
            home_team_name = home_team["name"],
            home_team_crest = home_team["crest"],
            home_team_goals_fulltime = int(score["fullTime"]['home']) - int(score["penalties"]['home']) if score['duration'] == 'PENALTY_SHOOTOUT' else score["fullTime"]['home'],
            home_team_goals_pens = score["penalties"]['home'] if score['duration'] == 'PENALTY_SHOOTOUT' else 0,
            away_team_name = away_team["name"],
            away_team_crest = away_team["crest"],
            away_team_goals_fulltime = int(score["fullTime"]['away']) - int(score["penalties"]['away']) if score['duration'] == 'PENALTY_SHOOTOUT' else score["fullTime"]['away'],
            away_team_goals_pens = score["penalties"]["away"] if score['duration'] == 'PENALTY_SHOOTOUT' else 0,
            match_duration = score['duration'],
            stage = match["stage"],
            status = match["status"]
        )
        new_match.save()
    else:
        old_match = Event.objects.get(match_id = match["id"])
        if (old_match.calendar != user_calendar) and (old_match.calendar2 is None):
            old_match.calendar2 = user_calendar
        elif (old_match.calendar2 != user_calendar) and (old_match.calendar is None):
            old_match.calendar = user_calendar

        #realistically only these can update for a match
        old_match.title = f"{home_team["name"]} vs {away_team["name"]}"
        old_match.status = match["status"]
        old_match.date_time = datetime.datetime.strptime(date_time_of_match, '%Y-%m-%dT%H:%M:%SZ')
        old_match.match_type = match_type
        if score['duration'] == 'PENALTY_SHOOTOUT':
            old_match.home_team_goals_fulltime = int(score["fullTime"]['home']) - int(score["penalties"]['home'])
            old_match.away_team_goals_fulltime = int(score["fullTime"]['away']) - int(score["penalties"]['away'])
            old_match.home_team_goals_pens = score["penalties"]['home']
            old_match.away_team_goals_pens = score["penalties"]["away"]
        else:
            old_match.home_team_goals_fulltime = score["fullTime"]['home']
            old_match.away_team_goals_fulltime = score["fullTime"]['away']

        old_match.home_team_name = home_team["name"]
        old_match.away_team_name = away_team["name"]
        old_match.home_team_crest = home_team["crest"]
        old_match.stage = match["stage"]
        old_match.match_duration = score['duration']
        old_match.away_team_crest = away_team["crest"]
        old_match.save()

@login_required
def event_reminder(request):
    user_club = request.user.club
    user_timezone = request.user.time_zone
    user_calendar = Calendar.objects.get(club = user_club)
    players_of_club = User.objects.filter(club = user_club, is_coach = False)
    current_datetime = datetime.datetime.now(pytz.timezone(user_timezone))
    current_month = current_datetime.month
    current_year = current_datetime.year
    coach = User.objects.get(club = user_club, is_coach = True)
    if current_month >= 9:
        if current_month >= 11:
            next_month = current_month - 12 + 2
            next_year = current_year + 1
            ending_datetime = datetime.datetime(next_year, next_month, 1)
        else:
            next_month = current_month + 2
            ending_datetime = datetime.datetime(current_year, next_month, 1)
    else:
        next_month = current_month + 2
        ending_datetime = datetime.datetime(current_year, next_month, 1)

    upcoming_events = (Event.objects.filter(calendar = user_calendar, date_time__range = [current_datetime, ending_datetime]) | Event.objects.filter(calendar2 = user_calendar, date_time__range = [current_datetime, ending_datetime])).order_by('date_time')

    if request.method == "POST":
        player_email_list = request.POST.getlist('player_emails')
        event_id = request.POST['selected_event']
        event = Event.objects.get(pk = event_id)
        local_datetime = event.date_time.astimezone(pytz.timezone(user_timezone)).strftime("%B %d, %Y, %I:%M %p,")
        if event.event_type != "Match":
            subject = f"Reminder from coach {coach} of {event.event_type} session soon"
            message = f"You have a {event.event_type} session on {local_datetime} {request.user.time_zone} timing. \n\nDo not forget or there will be consequences"
        else:
            subject = f"Reminder from coach {coach} of match soon"
            message = f"Matchday!\n\nYou have a match on {local_datetime} {request.user.time_zone} timing.\n\n{event.home_team_name} vs {event.away_team_name}\n\nDo not forget or there will be consequences"
        from_email = 'totslewanah@gmail.com'
        send_mail(subject, message, from_email, player_email_list)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'training/reminder.html', {
            "player_list": players_of_club,
            "upcoming_events": upcoming_events,
            "user_timezone": user_timezone
        })
@login_required
def update_timezone(request):
    if request.method == "POST":
        new_timezone = request.POST['user_time_zone']
        user = User.objects.get(id = request.user.id)
        user.time_zone = new_timezone
        user.save()
    user_current_datetime = datetime.datetime.now(pytz.timezone(request.user.time_zone))
    month_num = user_current_datetime.month
    year = user_current_datetime.year

    return HttpResponseRedirect(reverse(schedule, kwargs={
        "month_num": month_num, "year": year
    }))