import json

"""



example of scores sent from frontend :

[
    {
        "player_id": "player_1",
        "Content/Argument": 8,
        "Clarity & Articulation": 7,
        "Rebuttal": 9,
        "Body Language": 6,
        "Time Management": 8
    },
    {
        "player_id": "player_2",
        "Content/Argument": 9,
        "Clarity & Articulation": 8,
        "Rebuttal": 7,
        "Body Language": 8,
        "Time Management": 9
    },
    {
        "player_id": "player_3",
        "Content/Argument": 6,
        "Clarity & Articulation": 6,
        "Rebuttal": 7,
        "Body Language": 7,
        "Time Management": 6
    }
]

Pre defiled weightages :

    weights = {
    "Content/Argument": 0.30, (30% / 100)
    "Clarity & Articulation": 0.20,
    "Rebuttal": 0.20,
    "Body Language": 0.15,
    "Time Management": 0.15,
}



"""


def calculate_scores(request):
    subevent_happening = request.GET.get('subevent')
    scores = request.GET.get('scores')
    round_number = int(request.GET.get('round', 1))  # Default to round 1
    number_of_team_to_be_selected_for_next_round = int(request.GET.get('number_of_team_to_be_selected_for_next_round', 0))

    if not scores or not subevent_happening:
        return JsonResponse({"error": "Missing required parameters"}, status=400)

    # Parse scores from JSON
    scores = json.loads(scores)
    final_scores_with_player_id = []


    # Define criteria weights for each event
    criteria_weights = {
        "Debate": {
            "Content/Argument": 0.30,
            "Clarity & Articulation": 0.20,
            "Rebuttal": 0.20,
            "Body Language": 0.15,
            "Time Management": 0.15,
        },
        "Elocution": {
            "Content": 0.30,
            "Pronunciation & Clarity": 0.20,
            "Expression & Voice Modulation": 0.20,
            "Confidence & Stage Presence": 0.15,
            "Time Management": 0.15,
        },
        "Quiz": {
            "Knowledge": 0.50,
            "Speed": 0.20,
            "Team Coordination": 0.20,
            "Behavior & Conduct": 0.10,
        },
        "Blog Writing": {
            "Content": 0.40,
            "Structure": 0.20,
            "Language": 0.20,
            "Engagement": 0.10,
            "Relevance": 0.10,
        },
    
        "Calligraphy (Hindi)": {
            "Letter Formation": 0.30,
            "Layout & Spacing": 0.20,
            "Creativity": 0.20,
            "Presentation": 0.15,
            "Time Management": 0.15,
        },

        "Mr. & Mrs. Aurora": {
            "Introduction Round": 0.20,
            "Talent Round": 0.25,
            "Q&A Round": 0.30,
            "Presentation": 0.15,
            "Audience Impact": 0.10,
        },
        "Cooking Without Fire/Mocktail": {
            "Taste & Presentation": 0.30,
            "Creativity": 0.25,
            "Cleanliness & Hygiene": 0.20,
            "Time Management": 0.15,
            "Relevance": 0.10,
        },
        "Poster Making": {
            "Creativity": 0.30,
            "Relevance": 0.25,
            "Presentation": 0.20,
            "Color Scheme": 0.15,
            "Time Management": 0.10,
        },
        "Face Painting": {
            "Creativity & Concept": 0.30,
            "Color Combination": 0.25,
            "Neatness": 0.20,
            "Relevance": 0.15,
            "Time Management": 0.10,
        },
        "Rangoli Making": {
            "Design & Pattern": 0.30,
            "Color Combination": 0.20,
            "Neatness": 0.20,
            "Theme Relevance": 0.15,
            "Time Management": 0.15,
        },
        "Fabric Painting": {
            "Design & Creativity": 0.30,
            "Color Combination": 0.25,
            "Neatness": 0.20,
            "Relevance": 0.15,
            "Time Management": 0.10,
        },
        "Mehendi": {
            "Design Complexity": 0.30,
            "Neatness": 0.20,
            "Speed": 0.20,
            "Creativity": 0.15,
            "Theme Relevance": 0.15,
        },
        "Solo Singing": {
            "Vocal Quality": 0.30,
            "Song Selection": 0.20,
            "Expression & Stage Presence": 0.20,
            "Rhythm & Tempo": 0.15,
            "Audience Impact": 0.15,
        },
        "Solo Dance": {
            "Choreography": 0.30,
            "Expression": 0.25,
            "Stage Presence": 0.20,
            "Timing & Rhythm": 0.10,
            "Audience Impact": 0.15,
        },
        "Group Dance": {
            "Coordination": 0.30,
            "Choreography": 0.25,
            "Costume": 0.15,
            "Audience Impact": 0.30, 
        },

        "Flashmob": {
            "Surprise Element": 0.30,
            "Energy & Enthusiasm": 0.25,
            "Choreography": 0.20,
            "Audience Impact": 0.10,
            "Time Management": 0.10,
        },
        "Drama/Mono Acting": {
            "Script": 0.30,
            "Expression": 0.25,
            "Dialogue Delivery": 0.20,
            "Stage Presence": 0.15,
            "Theme Relevance": 0.10,
        },
        "Fashion Show": {
            "Costume & Styling": 0.30,
            "Walk & Confidence": 0.25,
            "Expression & Posing": 0.20,
            "Audience Impact": 0.10,
            "Relevance to Theme": 0.10,
        },
        "Instrumental": {
            "Technical Skill": 0.30,
            "Presentation": 0.25,
            "Expression": 0.20,
            "Rhythm & Tempo": 0.15,
            "Audience Impact": 0.10,
        },
        "Spot Photography": {
            "Composition": 0.30,
            "Creativity": 0.25,
            "Storytelling": 0.20,
            "Presentation": 0.15,
            "Theme Relevance": 0.10,
        },
        "Film Making": {
            "Script/Storyline": 0.30,
            "Direction": 0.25,
            "Cinematography": 0.20,
            "Post-Production": 0.15,
            "Storytelling": 0.10,
        },
        "Department Parade": {
            "Discipline": 0.30,
            "Coordination": 0.25,
            "Presentation": 0.20,
            "Synchronization": 0.15,
            "Impact": 0.10,
        },
        "Shark Tank": {
            "Idea & Innovation": 0.30,
            "Presentation": 0.25,
            "Business Feasibility": 0.20,
            "Q&A Round": 0.15,
            "Innovation": 0.10,
        },
        "Standup/Mimicry": {
            "Humor & Content": 0.30,
            "Delivery": 0.25,
            "Stage Presence": 0.20,
            "Content Originality": 0.15,
            "Audience Interaction": 0.10,
        },
        "Group Singing": {
            "Vocal Quality": 0.30,
            "Song Selection": 0.20,
            "Expression & Stage Presence": 0.20,
            "Rhythm & Tempo": 0.15,
            "Theme Relevance": 0.10,
        },
        "Duet Dance": {
            "Choreography": 0.30,
            "Expression": 0.25,
            "Costume": 0.15,
            "Timing & Rhythm": 0.10,
            "Audience Impact": 0.10,
        },


        
        "Reel Making": {
            "Creativity": 0.30,
            "Relevance": 0.25,
            "Editing & Transitions": 0.20,
            "Audience Engagement": 0.15,
            "Theme Relevance": 0.10,
        },
    }

    if subevent_happening not in criteria_weights:
        return JsonResponse({"error": f"Invalid subevent: {subevent_happening}"}, status=400)

    weights = criteria_weights[subevent_happening]

    # Calculate total scores
    for one_player in scores:
        player_id = one_player['player_id']
        total_score = sum(
            one_player[criterion] * weights[criterion]
            for criterion in weights if criterion in one_player
        )
        final_scores_with_player_id.append({
            "player_id": player_id,
            "total_score": total_score,
        })

    # Sort players by total score (descending)
    final_scores_with_player_id.sort(key=lambda x: x['total_score'], reverse=True)

    # Select top teams if needed
    selected_players = []
    if number_of_team_to_be_selected_for_next_round > 0:
        selected_players = final_scores_with_player_id[:number_of_team_to_be_selected_for_next_round]

    # Save scores to the database
    for player in final_scores_with_player_id:
        result, created = Results.objects.update_or_create(
            subevent=subevent_happening,
            player_id=player['player_id'],
            round_number=round_number,
            defaults={
                "total_score": player['total_score'],
                "next_round": player in selected_players,
            }
        )

    # Return the response
    return JsonResponse({
        "scores": final_scores_with_player_id,
        "selected_for_next_round": selected_players,
    })
    

# Example for scores storing # database 

class results():
    subevent = foreign_key
    player_id = foreign_key
    total_score = models.FloatField()
    next_round = models.BooleanField(default=False)
    round_number = models.IntegerField(default=1)




