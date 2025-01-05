from django import template

register = template.Library()

@register.filter
def get_score(scores_dict, subevent_id):
    """Get scores for a specific subevent"""
    if not scores_dict:
        return {}
    return scores_dict.get(str(subevent_id), {})

@register.filter
def get_group_score(subevent_scores, group):
    """Get score for a specific group in a subevent"""
    if not subevent_scores or not group:
        return '-'
    key = f"{group['year']}_{group['department']}_{group['division']}"
    return subevent_scores.get(key, '-')