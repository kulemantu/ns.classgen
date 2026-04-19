"""Data access layer for ClassGen.

Re-exports all public functions for convenience so callers can do:
    from classgen.data import save_teacher, log_session, ...
"""

from .client import supabase
from .homework import (
    HOMEWORK_CODE_TTL_DAYS,
    get_homework_code,
    list_homework_codes_for_teacher,
    save_homework_code,
)
from .lessons import (
    cache_lesson,
    get_cached_lesson,
    get_covered_topics,
    log_lesson_generated,
)
from .parents import (
    list_parent_subscriptions,
    save_parent_subscription,
    unsubscribe_parent,
)
from .push import (
    get_push_subscriptions,
    remove_push_subscription,
    save_push_subscription,
)
from .quiz import (
    count_quiz_submissions_for_codes,
    get_class_leaderboard,
    get_quiz_results,
    get_student_progress,
    save_quiz_submission,
)
from .schools import (
    get_school,
    get_school_teachers,
    save_school,
)
from .sessions import (
    clear_session_history,
    get_session_history,
    log_session,
)
from .subscriptions import (
    get_subscription,
    get_weekly_usage,
    log_usage,
    save_subscription,
)
from .teachers import (
    add_teacher_class,
    get_teacher_by_phone,
    get_teacher_by_slug,
    get_teacher_lesson_stats,
    remove_teacher_class,
    save_teacher,
    update_teacher_country,
    update_teacher_name,
)
from .threads import (
    get_active_thread,
    set_active_thread,
)
from .wa_flows import (
    WAFlow,
    clear_flow,
    get_flow,
    set_flow,
    update_flow,
)

__all__ = [
    # client
    "supabase",
    # sessions
    "log_session",
    "get_session_history",
    "clear_session_history",
    # teachers
    "save_teacher",
    "get_teacher_by_phone",
    "get_teacher_by_slug",
    "add_teacher_class",
    "remove_teacher_class",
    "update_teacher_name",
    "update_teacher_country",
    "get_teacher_lesson_stats",
    # homework
    "HOMEWORK_CODE_TTL_DAYS",
    "save_homework_code",
    "get_homework_code",
    "list_homework_codes_for_teacher",
    # quiz
    "save_quiz_submission",
    "get_quiz_results",
    "get_student_progress",
    "count_quiz_submissions_for_codes",
    "get_class_leaderboard",
    # lessons
    "log_lesson_generated",
    "get_covered_topics",
    "get_cached_lesson",
    "cache_lesson",
    # subscriptions
    "get_subscription",
    "save_subscription",
    "log_usage",
    "get_weekly_usage",
    # schools
    "save_school",
    "get_school",
    "get_school_teachers",
    # parents
    "save_parent_subscription",
    "list_parent_subscriptions",
    "unsubscribe_parent",
    # push
    "save_push_subscription",
    "get_push_subscriptions",
    "remove_push_subscription",
    # threads
    "set_active_thread",
    "get_active_thread",
    # wa_flows
    "WAFlow",
    "set_flow",
    "get_flow",
    "update_flow",
    "clear_flow",
]
