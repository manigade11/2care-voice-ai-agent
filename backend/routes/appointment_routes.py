from fastapi import APIRouter
from backend.controllers.appointment_controller import (
    check_availability,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    get_appointment,
    list_appointments,
    trigger_campaign,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

router.add_api_route("/availability", check_availability, methods=["POST"])
router.add_api_route("/book", book_appointment, methods=["POST"])
router.add_api_route("/cancel", cancel_appointment, methods=["POST"])
router.add_api_route("/reschedule", reschedule_appointment, methods=["POST"])
router.add_api_route("/campaign/trigger", trigger_campaign, methods=["POST"])
router.add_api_route("", list_appointments, methods=["GET"])
router.add_api_route("/{appointment_id}", get_appointment, methods=["GET"])