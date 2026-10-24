# AI Property-Management Email Router

An AI assistant that triages incoming tenant and prospect emails for a property manager. It classifies each email with an LLM, logs it as a ticket, routes it to the right team, and drafts a reply. A live dashboard shows all incoming requests, prioritised by urgency.

The idea comes from my own experience managing a 100+ unit student residence, where sorting and answering tenant messages took up a large part of the day.

> **Status: work in progress.** The classification, logging, routing and dashboard work end to end; the data-lookup tools are still mocked (see below).

## How it works

```
Gmail ──▶ Pipedream webhook ──▶ Flask app (router.py) ──▶ Gemini
                                        │
                                        ├──▶ Google Sheets (ticket log)
                                        └──▶ reply text back to the sender
Google Sheets ──▶ Streamlit dashboard (dashboard.py)
```

1. **Classification:** Gemini 2.5 Flash reads the email and returns structured JSON (enforced with a response schema): one of 8 categories (e.g. *Maintenance – Emergency*, *Rental Inquiry*, *Billing*, *Tenant Complaint*), an urgency level, the unit, a one-sentence summary and, for maintenance, the trade needed (plumbing, electrical, HVAC…).
2. **Routing and replies:** maintenance, complaints and administrative questions get an immediate templated reply and are flagged for the right team. Rental inquiries and general questions go to a second step with tool calling (Gemini 2.5 Pro), where the model can choose to look up unit availability in a spreadsheet (`query_data_file`) or search a policy document (`search_knowledge_base`).
3. **Logging:** every ticket is appended to a Google Sheet with a timestamp and sender.
4. **Dashboard:** a Streamlit app reads the sheet and shows all requests with summary counts, colour-coded by urgency, and sortable.

A `MOCK_MODE` switch lets the whole pipeline run without spending API quota.

## Status and next steps

- [x] JSON-schema classification of emails
- [x] Webhook endpoint, Google Sheets logging and routing
- [x] Streamlit dashboard
- [ ] Execute the lookup tools for real (currently they return placeholder output)
- [ ] Evaluation: measure classification accuracy on a labelled test set of emails
- [ ] Send replies automatically and add a human-approval step for sensitive cases

## How I built it

The code was written with AI coding assistants. I chose the approach, set up and connected the services (Gmail, Pipedream, Gemini, Google Sheets, PythonAnywhere), and did the testing and debugging to get the pipeline running end to end.

## Running it

```
pip install -r requirements.txt
cp .env.example .env          # add your Gemini API key
# add a Google service-account key as service_account.json (never commit it)
flask --app router run        # the webhook
streamlit run dashboard.py    # the dashboard
```

`your_data.csv` contains made-up sample unit data.
