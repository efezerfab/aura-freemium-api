import os
from flask import Flask, request, jsonify
from database_freemium_methods import db
from tiktok_webhook import verify_tiktok_signature, parse_tiktok_lead
from typeform_webhook import parse_typeform_lead

app = Flask(__name__)

# Initialise table on startup
db.init_table()


# ── Health check ────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "aura-freemium"}), 200


# ── TikTok Lead Gen webhook ─────────────────────────────────────────────────

@app.route("/tiktok-lead", methods=["POST"])
def tiktok_lead():
    """
    TikTok POSTs here when a user submits the Lead Gen form.
    Must respond within 3 seconds — do heavy work asynchronously.
    """
    payload_bytes = request.get_data()
    signature = request.headers.get("X-TikTok-Signature", "")

    if not verify_tiktok_signature(payload_bytes, signature):
        return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    lead = parse_tiktok_lead(payload)

    if not lead.get("email"):
        return jsonify({"error": "no email in payload"}), 400

    lead_id = db.save_lead(lead)
    # lead_id is None on duplicate — still return 200 so TikTok doesn't retry
    return jsonify({"ok": True, "lead_id": lead_id}), 200


# ── Typeform webhook ────────────────────────────────────────────────────────

@app.route("/typeform-lead", methods=["POST"])
def typeform_lead():
    """
    Typeform POSTs here when a user submits the freemium form.
    Payload is standard Typeform webhook JSON.
    """
    payload = request.get_json(force=True, silent=True) or {}
    lead = parse_typeform_lead(payload)

    if not lead.get("email"):
        return jsonify({"error": "no email in payload"}), 400

    lead_id = db.save_lead(lead)
    return jsonify({"ok": True, "lead_id": lead_id}), 200


# ── Agent App polling endpoints ─────────────────────────────────────────────

@app.route("/admin/pending-leads", methods=["GET"])
def pending_leads():
    """Agent App polls this to find new leads to process."""
    leads = db.get_pending_leads()
    return jsonify([dict(r) for r in leads]), 200


@app.route("/admin/lead-status/<int:lead_id>", methods=["PATCH"])
def update_lead_status(lead_id):
    """
    Agent App calls this after sending a report.
    Body: {"status": "report_sent"}
    Valid statuses: processed | report_sent | upsell_sent | failed
    """
    body = request.get_json(force=True, silent=True) or {}
    status = body.get("status")
    if not status:
        return jsonify({"error": "status required"}), 400
    db.update_status(lead_id, status)
    return jsonify({"ok": True}), 200


@app.route("/admin/all-leads", methods=["GET"])
def all_leads():
    limit = int(request.args.get("limit", 100))
    leads = db.get_all_leads(limit=limit)
    return jsonify([dict(r) for r in leads]), 200


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
