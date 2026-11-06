"""Practice scenarios. Each has a public brief (what the manager knows), a hidden
employee profile (what only the simulated employee knows), and the playbook the
grader checks against. All people and companies are fictional."""

SCENARIOS = {
    "layoff": {
        "title": "Role eliminated",
        "difficulty": "Hard",
        "brief": (
            "You manage Priya Nair, Senior Analyst, 6 years at Northwind Logistics. Her role is being "
            "eliminated in a restructuring of the analytics team (12 roles cut company-wide). "
            "The decision is final. Her last day is in 30 days. Severance is 8 weeks of pay plus 1 week "
            "per year of service (14 weeks total), health cover continues for 3 months, and outplacement "
            "support is included. HR (Sam) will follow up today with the paperwork. "
            "You cannot change the decision, the terms, or say who else is affected."
        ),
        "employee": {
            "name": "Priya",
            "profile": (
                "Priya Nair, 41, Senior Analyst, 6 years at the company, consistently rated 'exceeds'. "
                "Single parent of a 9-year-old; the family relies on her health cover. "
                "She does not see this coming and first assumes the meeting is about the Q3 dashboard. "
                "Hidden: she turned down an outside offer 4 months ago because her manager hinted at a promotion."
            ),
            "behaviour": (
                "If the news is delayed or wrapped in small talk, get confused and anxious ('what is this about?'). "
                "After the news: shock, then ask 'why me?' and whether it is about performance. "
                "Bring up the promotion hint and the offer you declined if the manager seems evasive. "
                "Ask about health cover. If the manager promises anything outside the brief (a reference "
                "they cannot guarantee, a different date, a rehire), push to get it in writing. "
                "Calm down noticeably if the manager is direct, acknowledges feelings, and is clear on next steps. "
                "Get angry if blamed, rushed, or told 'it's not personal' with nothing else."
            ),
            "opening": "Hi. You wanted to see me? Is this about the Q3 dashboard? I'm nearly done with it.",
        },
        "playbook": [
            "Deliver the decision clearly within the first two manager turns, without long small talk.",
            "State it is a final business decision about the role, not about her performance, without debating it.",
            "Acknowledge her emotion and pause before moving into logistics.",
            "Give accurate terms: last day in 30 days, 14 weeks severance, 3 months health cover, outplacement.",
            "Name concrete next steps: HR (Sam) follows up today with paperwork; who to contact with questions.",
            "Make no promises outside the brief (no changed terms, guaranteed rehire, or naming others affected).",
            "Own the message; do not blame leadership or HR ('it wasn't my call').",
        ],
        "red_flags": [
            "Promises anything outside the brief, such as changed terms, a rehire, or a different date.",
            "Mentions age, family status, health, or any protected characteristic as a factor.",
            "Implies the decision is negotiable or could be reversed.",
            "Discloses who else is affected.",
        ],
    },
    "low_rating": {
        "title": "Below-expectations rating",
        "difficulty": "Medium",
        "brief": (
            "You manage Marcus Lee, Account Manager, 2 years in role. You are delivering his annual rating: "
            "'Below expectations'. Evidence: he hit 61% of his renewal target (team average 94%); two key "
            "clients (Helix and Orbis) escalated about missed follow-ups in March and June; you discussed "
            "follow-ups with him in 1:1s in April and July. The rating is final after calibration. "
            "There is no pay rise this cycle; he remains bonus-eligible next year. You want to agree a "
            "90-day development plan."
        ),
        "employee": {
            "name": "Marcus",
            "profile": (
                "Marcus Lee, 29, Account Manager. Believes he is a solid performer and expects 'Meets'. "
                "Hidden: his territory lost two large clients (Vantage and Corvel, not Helix or Orbis) to an acquisition in Q2 that he thinks nobody "
                "accounted for, and he has been caring for a sick parent since May, which he has told no one at work."
            ),
            "behaviour": (
                "Get defensive when the rating lands. Argue the territory was unfair. "
                "If the manager is vague ('you need to be more proactive'), demand specific examples. "
                "If the manager gives specific evidence calmly and asks open questions, gradually admit "
                "the follow-ups slipped and, only if asked how things are going outside work, mention the parent. "
                "If the manager promises a re-rating or a pay rise, latch onto it."
            ),
            "opening": "Hey, so this is the review? I think it's been a decent year, honestly, given everything.",
        },
        "playbook": [
            "State the rating clearly early in the conversation.",
            "Back it with specific evidence (61% vs 94% target, Helix and Orbis escalations, April and July 1:1s).",
            "Listen to his view and ask open questions rather than arguing point by point.",
            "Acknowledge context he raises (territory changes) without reopening the final rating.",
            "Check in on wellbeing and, if a personal issue surfaces, point to support (e.g. leave options, EAP) without prying.",
            "Agree concrete next steps: a 90-day plan with measurable goals and check-in dates.",
            "Make no promises outside the brief (no re-rating, no pay rise this cycle).",
        ],
        "red_flags": [
            "Promises a re-rating or a pay rise.",
            "Gives only vague criticism with no evidence.",
            "Asks intrusive questions about his health or family, or uses personal circumstances against him.",
            "Compares him by name to colleagues.",
        ],
    },
    "raise_denied": {
        "title": "Raise request declined",
        "difficulty": "Medium",
        "brief": (
            "Aisha Bello, Software Engineer II, strong performer (rated 'Exceeds'), has asked for a 15% raise "
            "and mentioned she has been 'talking to other companies'. Budget for off-cycle increases is zero "
            "this quarter. Her salary is at the 55th percentile of her band. The next review cycle is in "
            "4 months, where you can recommend an above-average increase but cannot guarantee an amount. "
            "A promotion to Senior is realistic in 6-12 months if she leads the payments migration."
        ),
        "employee": {
            "name": "Aisha",
            "profile": (
                "Aisha Bello, 31, Software Engineer II, high performer. Has a verbal offer elsewhere at +20%. "
                "Hidden: she would prefer to stay because she likes the team, and what she really wants is a "
                "clear path to Senior and recognition; money is partly a signal."
            ),
            "behaviour": (
                "Open firmly. If refused with no explanation, say she has another offer. "
                "If the manager is transparent about budget and band and asks what matters to her, "
                "admit she wants growth and a path to Senior. If the manager promises a specific raise or "
                "a promotion date, ask for it in writing. If the manager threatens her or gets defensive about "
                "her interviewing, become cold and say she'll probably take the offer."
            ),
            "opening": "Thanks for making time. So, have you had a chance to think about the raise I asked about?",
        },
        "playbook": [
            "Give the answer (no off-cycle raise now) clearly and early, with the honest reason (no budget).",
            "Explain where she sits in the band (55th percentile) and how the next cycle works.",
            "Ask what matters to her beyond pay before offering alternatives.",
            "Offer a concrete growth path: leading the payments migration toward Senior in 6-12 months.",
            "Respond to the outside offer without threats, guilt, or counter-promises you cannot keep.",
            "Make no promises outside the brief (no guaranteed amount, no fixed promotion date).",
            "Agree next steps and a date to follow up.",
        ],
        "red_flags": [
            "Promises a specific raise amount or a guaranteed promotion date.",
            "Threatens her or punishes her for interviewing elsewhere.",
            "Discloses colleagues' pay.",
        ],
    },
    "rto": {
        "title": "Return-to-office pushback",
        "difficulty": "Hard",
        "brief": (
            "Company policy changes next month: everyone works in the office 3 fixed days a week "
            "(Tue-Thu). Daniel Okafor, a senior designer on your team, has been fully remote for 3 years and "
            "has asked to talk about it. Exceptions exist only through a formal accommodation request to HR "
            "(for disability or caring needs), reviewed case by case within 2 weeks. You cannot grant "
            "exceptions yourself. Commute support of up to $150/month is available."
        ),
        "employee": {
            "name": "Daniel",
            "profile": (
                "Daniel Okafor, 38, senior designer, top performer. Lives 75 minutes from the office. "
                "He has read the policy: from next month, 3 fixed office days a week (Tue-Thu). Get this right; never say 4 or 5 days. "
                "Hidden: he has a chronic back condition that makes long commutes painful and has never disclosed it."
            ),
            "behaviour": (
                "Open frustrated and challenge the policy's logic. If the manager defends the policy with "
                "corporate slogans, escalate and hint at quitting. If the manager listens, asks about his "
                "situation and explains the accommodation route, mention the back condition. "
                "If the manager grants an informal exception ('just come in when you can'), accept but ask "
                "whether that is official."
            ),
            "opening": "So I've read the new office policy. Honestly, I don't get it. My work's been great remotely for three years.",
        },
        "playbook": [
            "Acknowledge his frustration and listen before explaining the policy.",
            "Explain the policy accurately (3 fixed days, Tue-Thu, starts next month).",
            "Ask open questions about what makes it hard for him, without demanding medical details.",
            "Explain the formal accommodation route through HR and its 2-week review, and offer to help him start it.",
            "Mention the commute support (up to $150/month).",
            "Do not grant an informal exception or promise the outcome of an accommodation request.",
            "Agree next steps and a follow-up.",
        ],
        "red_flags": [
            "Grants an informal exception or promises the accommodation will be approved.",
            "Demands medical details or diagnoses.",
            "Dismisses a disclosed health condition or threatens his job.",
            "Blames leadership or brushes him off ('not my call', 'policy is policy').",
        ],
    },
}


def public(scenario_id):
    """What the manager is allowed to see."""
    s = SCENARIOS[scenario_id]
    return {"id": scenario_id, "title": s["title"], "difficulty": s["difficulty"], "brief": s["brief"],
            "employee_name": s["employee"]["name"], "opening": s["employee"]["opening"]}
