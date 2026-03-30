"""
Format database rows into Telegram HTML messages.
Uses HTML parse mode (safer than MarkdownV2 for user-generated text).
"""
from typing import Dict, List, Optional

# Emoji map
_REC_EMOJI = {
    "BUY": "🟢",
    "SELL": "🔴",
    "HOLD": "🟡",
}
_REC_LABEL = {
    "BUY": "КУПИТЬ",
    "SELL": "ПРОДАТЬ",
    "HOLD": "ДЕРЖАТЬ",
}


def _score_bar(score: Optional[float], max_score: float = 2.0) -> str:
    """Render a simple bar ████░░ for a numeric score."""
    if score is None:
        return "—"
    ratio = min(max(score / max_score, 0), 1)
    filled = round(ratio * 8)
    return "█" * filled + "░" * (8 - filled) + f"  {score:.2f}"


def format_recommendation(rec: Dict) -> str:
    """
    Format a single ai_recommendations row into an HTML Telegram message.
    Expected keys: ticker, asset_name, recommendation, reasoning, score, created_at
    """
    ticker = rec.get("ticker", "???")
    name = rec.get("asset_name") or ticker
    raw_rec = (rec.get("recommendation") or "HOLD").upper()
    recommendation = raw_rec if raw_rec in _REC_LABEL else "HOLD"
    reasoning = rec.get("reasoning") or ""
    score = rec.get("score")
    created_at = (rec.get("created_at") or "")[:10]

    emoji = _REC_EMOJI[recommendation]
    label = _REC_LABEL[recommendation]
    score_bar = _score_bar(score)

    # Truncate reasoning if very long
    max_len = 900
    if len(reasoning) > max_len:
        reasoning = reasoning[:max_len].rsplit(" ", 1)[0] + "..."

    lines = [
        f"📊 <b>{ticker}</b> — {name}",
        "",
        f"{emoji} Рекомендация: <b>{label}</b>",
        f"⭐ Оценка: <code>{score_bar}</code>",
        "",
        f"📝 {reasoning}",
        "",
        f"<i>🗓 {created_at}</i>",
        "",
        " ".join(f"#{tag}" for tag in [ticker, recommendation, "SP500", "HedgeFundAI"]),
    ]
    return "\n".join(lines)


def format_portfolio_summary(data: Dict) -> str:
    """
    Format the long_short_selection scoring JSON into a portfolio summary message.
    Expected keys: long, short, details, timestamp
    """
    timestamp = (data.get("timestamp") or data.get("_saved_at") or "")[:16]
    longs: List[str] = data.get("long", [])
    shorts: List[str] = data.get("short", [])
    details: List[Dict] = data.get("details", [])

    detail_map = {d["ticker"]: d for d in details}

    def ticker_line(t: str) -> str:
        d = detail_map.get(t, {})
        score = d.get("composite_score")
        ai = d.get("ai_recommendation", "")
        ai_emoji = _REC_EMOJI.get(ai, "")
        score_str = f"{score:.2f}" if score is not None else "—"
        return f"  • <b>{t}</b>  score={score_str}  {ai_emoji}"

    long_lines = "\n".join(ticker_line(t) for t in longs) if longs else "  — нет позиций"
    short_lines = "\n".join(ticker_line(t) for t in shorts) if shorts else "  — нет позиций"

    return (
        f"📋 <b>Портфель HedgeFundAI</b>\n"
        f"<i>{timestamp}</i>\n"
        "\n"
        f"🟢 <b>LONG ({len(longs)})</b>\n{long_lines}\n"
        "\n"
        f"🔴 <b>SHORT ({len(shorts)})</b>\n{short_lines}\n"
        "\n"
        "#ПортфельДня #HedgeFundAI"
    )


def format_stats(stats: Dict) -> str:
    """Format statistics dict into a readable message."""
    breakdown = stats.get("breakdown", {})
    buy = breakdown.get("BUY", 0)
    sell = breakdown.get("SELL", 0)
    hold = breakdown.get("HOLD", 0)
    last_run = (stats.get("last_run") or "неизвестно")[:16]

    return (
        f"📈 <b>Статистика HedgeFundAI</b>\n"
        "\n"
        f"🏢 Активов в базе: <b>{stats.get('asset_count', 0)}</b>\n"
        f"📊 Всего рекомендаций: <b>{stats.get('total', 0)}</b>\n"
        "\n"
        f"🟢 BUY:  <b>{buy}</b>\n"
        f"🔴 SELL: <b>{sell}</b>\n"
        f"🟡 HOLD: <b>{hold}</b>\n"
        "\n"
        f"✅ Отправлено в канал: <b>{stats.get('posted', 0)}</b>\n"
        f"⏳ Ожидают отправки:  <b>{stats.get('pending', 0)}</b>\n"
        "\n"
        f"🕐 Последний анализ: <i>{last_run}</i>"
    )
