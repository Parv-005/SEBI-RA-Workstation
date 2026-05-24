"""Thin wrappers around the template engine.

The actual formatting logic lives in ``utils.message_templates``.
These functions maintain the existing call signatures so that no
callers need to change.
"""

import logging

from utils.message_templates import (
    build_trade_context,
    build_update_context,
    load_template,
    render_template,
)

_logger = logging.getLogger(__name__)


def format_new_trade(trade: dict) -> str:
    template = load_template("new_trade")
    context = build_trade_context(trade)
    return render_template(template, context)


def format_trade_update(trade: dict, update: dict) -> str:
    template = load_template("update")
    context = build_update_context(trade, update)
    return render_template(template, context)
