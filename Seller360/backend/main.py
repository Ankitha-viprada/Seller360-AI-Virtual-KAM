
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# =========================================================
# 1. CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

DATA = json.loads(
    (BASE_DIR / "seller_data.json").read_text(encoding="utf-8")
)

app = FastAPI(
    title="Seller360 Virtual KAM",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# 2. REQUEST AND RESPONSE MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    session_id: Optional[str] = "demo"


class ChatResponse(BaseModel):
    reply: str
    insights: List[str]
    actions: List[Dict[str, str]]
    mode: str


# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def contains_any(message, keywords):
    message = message.lower()

    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

        if re.search(pattern, message):
            return True

    return False


def money(value):
    return f"₹{value:,.0f}"


def get_asp(period):
    return period.get(
        "asp",
        period.get("average_selling_price", 500)
    )


def get_seller_name():
    return DATA["seller"].get("seller_name", "Seller")


def pct_change(old, new):
    if old == 0:
        return 0

    return round(((new - old) / old) * 100, 1)


# =========================================================
# 4. BUSINESS ANALYSIS
# =========================================================

def analyze():

    old = DATA["periods"]["last_month"]
    new = DATA["periods"]["this_month"]

    sales_change = pct_change(
        old["sales"], new["sales"]
    )

    order_change = pct_change(
        old["orders"], new["orders"]
    )

    cancellation_delta = (
        new["cancellation_rate"]
        - old["cancellation_rate"]
    )

    stock_delta = (
        new["out_of_stock_products"]
        - old["out_of_stock_products"]
    )

    insights = [
        f"Sales decreased by {abs(sales_change)}% from "
        f"{money(old['sales'])} to {money(new['sales'])}.",

        f"Orders decreased by {abs(order_change)}% from "
        f"{old['orders']} to {new['orders']}.",

        f"Cancellation rate changed from "
        f"{old['cancellation_rate']}% to "
        f"{new['cancellation_rate']}%.",

        f"Out-of-stock products changed from "
        f"{old['out_of_stock_products']} to "
        f"{new['out_of_stock_products']}.",

        f"Average selling price remained at "
        f"{money(get_asp(old))}."
    ]

    actions = [
        {
            "priority": "HIGH",
            "title": "Restore availability of high-demand products",
            "detail": (
                "Identify top-selling products and replenish "
                "the most important unavailable products first."
            ),
            "why": (
                "Out-of-stock products increased, which may "
                "limit the ability to fulfil customer demand."
            )
        },
        {
            "priority": "HIGH",
            "title": "Investigate order cancellations",
            "detail": (
                "Review cancelled orders and group reasons "
                "such as stock mismatch, seller rejection, "
                "dispatch delay and customer cancellation."
            ),
            "why": (
                "Cancellation rate increased from 8% to 14%. "
                "The exact causes are not included in the dataset."
            )
        },
        {
            "priority": "MEDIUM",
            "title": "Improve product discovery",
            "detail": (
                "Review product titles, images, descriptions, "
                "attributes, impressions and conversion."
            ),
            "why": (
                "Order volume declined, but listing traffic "
                "and conversion data are not available."
            )
        }
    ]

    return {
        "seller": DATA["seller"],
        "metrics": {
            "last_month": old,
            "this_month": new
        },
        "changes": {
            "sales_pct": sales_change,
            "orders_pct": order_change,
            "cancellation_delta": cancellation_delta,
            "stock_delta": stock_delta,
            "revenue_difference": old["sales"] - new["sales"]
        },
        "insights": insights,
        "actions": actions,
        "assumptions": DATA.get("assumptions", [])
    }


# =========================================================
# 5. BASIC INTENT DETECTION
# =========================================================

def detect_basic_intent(message):

    m = message.lower().strip()

    # SELLER PROFILE
    if contains_any(m, [
        "what information",
        "what info",
        "what do you know",
        "what data",
        "my details",
        "about my account",
        "about my business",
        "seller details",
        "information do you have",
        "have on my"
    ]):
        return "profile"

    # PROFIT AND MARGINS
    if contains_any(m, [
        "profit",
        "profitability",
        "profit margin",
        "margins",
        "net income",
        "net profit"
    ]):
        return "profit"

    # CUSTOMER BEHAVIOUR
    if contains_any(m, [
        "customer behaviour",
        "customer behavior",
        "customer base",
        "customer retention",
        "repeat customers",
        "customer preferences",
        "customer acquisition",
        "customer feedback"
    ]):
        return "customers"

    # PRODUCT PERFORMANCE
    if contains_any(m, [
        "best selling product",
        "best seller",
        "top selling product",
        "worst performing product",
        "product performance",
        "which product",
        "individual product",
        "sku"
    ]):
        return "product_performance"

    # WEEKLY PLAN
    if contains_any(m, [
        "weekly plan",
        "weekly improvement",
        "plan for this week",
        "week plan"
    ]):
        return "weekly_plan"

    # SUMMARY
    if contains_any(m, [
        "summarize",
        "summarise",
        "summary",
        "recap",
        "overall performance"
    ]):
        return "summary"

    # SEASONAL DEMAND
    if contains_any(m, [
        "seasonal",
        "festival",
        "festive",
        "high demand season"
    ]):
        return "seasonal"

    # DISCOUNTS
    if contains_any(m, [
        "discount",
        "offer",
        "coupon",
        "promotional offer"
    ]):
        return "discounts"

    # LISTING QUALITY
    if contains_any(m, [
        "product image",
        "product images",
        "description",
        "title",
        "listing quality",
        "product listing",
        "conversion rate",
        "conversion"
    ]):
        return "listing"

    # VISIBILITY
    if contains_any(m, [
        "visibility",
        "traffic",
        "impression",
        "impressions",
        "views",
        "product views",
        "listing views",
        "discover my products",
        "find my products"
    ]):
        return "visibility"

    # CANCELLATIONS
    if contains_any(m, [
        "cancel",
        "cancellation",
        "return",
        "reject"
    ]):
        return "cancellations"

    # INVENTORY
    if contains_any(m, [
        "stock",
        "inventory",
        "out of stock",
        "restock",
        "replenish",
        "availability",
        "low stock",
        "running out"
    ]):
        return "inventory"

    # PRICING
    if contains_any(m, [
        "price",
        "pricing",
        "expensive",
        "cheap",
        "competitor price",
        "competitive pricing",
        "overpriced",
        "underpriced"
    ]):
        return "pricing"

    # ORDERS
    if contains_any(m, [
        "order",
        "orders",
        "order volume",
        "order conversion"
    ]):
        return "orders"

    # SALES DECLINE ANALYSIS
    if contains_any(m, [
        "why",
        "reason",
        "because",
        "explain why",
        "what caused",
        "cause of",
        "sales drop",
        "sales down",
        "sales decreased",
        "revenue drop",
        "revenue down",
        "revenue decreased",
        "revenue fallen",
        "sales fallen",
        "decline",
        "analyse",
        "analyze"
    ]):
        return "analysis"

    # ACTION PLAN
    if contains_any(m, [
        "improve",
        "increase",
        "grow",
        "boost",
        "what should i do",
        "how can i",
        "how should i",
        "recommend",
        "action plan",
        "next step",
        "suggestion",
        "help me",
        "opportunity",
        "opportunities"
    ]):
        return "action_plan"

    # REVENUE AND EARNINGS
    if contains_any(m, [
        "revenue",
        "sales",
        "earn",
        "earned",
        "earning",
        "earnings",
        "income",
        "turnover",
        "generated",
        "make money",
        "made money",
        "how much did i make",
        "how much did i earn"
    ]):

        # LAST MONTH
        if contains_any(m, [
            "last month",
            "previous month",
            "previous month's",
            "last month's",
            "last month revenue"
        ]):
            return "last_month_revenue"

        # THIS MONTH
        if contains_any(m, [
            "this month",
            "current month",
            "so far"
        ]):
            return "this_month_revenue"

        # REVENUE DIFFERENCE
        if contains_any(m, [
            "lost",
            "difference",
            "gap"
        ]):
            return "revenue_difference"

        return "revenue"

    # AVERAGE ORDER VALUE
    if contains_any(m, [
        "average order value",
        "value per order",
        "average value of orders"
    ]):
        return "average_order_value"

    # BUSINESS STRENGTHS
    if contains_any(m, [
        "strongest metric",
        "strongest metrics",
        "best metric",
        "best performing area",
        "doing well"
    ]):
        return "strengths"

    # GREETING
    if contains_any(m, [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good evening"
    ]):
        return "greeting"

    return "general"


# =========================================================
# 6. CONTEXTUAL INTENT DETECTION
# =========================================================

def detect_intent(message, history=None):

    intent = detect_basic_intent(message)

    if intent != "general":
        return intent

    history = history or []

    previous = history[:]

    # Remove current question if included in history
    if (
        previous
        and previous[-1].get("role") == "user"
        and previous[-1].get("content", "").strip().lower()
        == message.strip().lower()
    ):
        previous = previous[:-1]

    previous_intent = "general"

    for item in reversed(previous):

        if item.get("role") != "user":
            continue

        previous_intent = detect_basic_intent(
            str(item.get("content", ""))
        )

        if previous_intent != "general":
            break

    m = message.lower().strip()

    # PREVIOUS MONTH FOLLOW-UP
    if contains_any(m, [
        "previous month",
        "last month",
        "what about last month",
        "what about previous month"
    ]):

        if previous_intent in [
            "revenue",
            "this_month_revenue",
            "last_month_revenue"
        ]:
            return "last_month_revenue"

        if previous_intent == "orders":
            return "orders"

    # REVENUE OR SALES DECLINE FOLLOW-UP
    if contains_any(m, [
        "why",
        "why is that",
        "why has it",
        "explain why",
        "what caused this",
        "what caused that",
        "what is the reason"
    ]):

        if previous_intent in [
            "revenue",
            "last_month_revenue",
            "this_month_revenue",
            "orders",
            "summary"
        ]:
            return "analysis"

        if previous_intent == "cancellations":
            return "cancellations"

        if previous_intent == "inventory":
            return "inventory"

    # IMPACT FOLLOW-UP
    if contains_any(m, [
        "affecting my revenue",
        "affect revenue",
        "affecting sales",
        "affect my sales",
        "impact on revenue",
        "impact my sales"
    ]):
        if previous_intent in [
            "inventory",
            "cancellations",
            "orders"
        ]:
            return "impact"

    # SERIOUSNESS FOLLOW-UP
    if contains_any(m, [
        "is that serious",
        "is it serious",
        "is this a problem",
        "is that a problem",
        "should i worry"
    ]):
        if previous_intent in [
            "inventory",
            "cancellations"
        ]:
            return previous_intent

        return "analysis"

    # ACTION FOLLOW-UP
    if contains_any(m, [
        "what should i do now",
        "what do i do next",
        "what next",
        "how do i fix this",
        "how can i solve this",
        "now what"
    ]):
        return "action_plan"

    # EXPLANATION FOLLOW-UP
    if contains_any(m, [
        "tell me more",
        "explain more",
        "more details",
        "elaborate"
    ]):
        if previous_intent != "general":
            return previous_intent

    return "general"


# =========================================================
# 7. RULE-BASED RESPONSE ENGINE
# =========================================================

def fallback_reply(message, history=None):

    history = history or []

    intent = detect_intent(message, history)

    a = analyze()

    old = DATA["periods"]["last_month"]
    new = DATA["periods"]["this_month"]

    seller = DATA["seller"]
    seller_name = get_seller_name()

    last_asp = get_asp(old)
    current_asp = get_asp(new)

    # GREETING
    if intent == "greeting":

        return (
            f"Hello {seller_name}! Welcome to Seller360. "
            "I'm your AI Virtual Key Account Manager. "
            "I can help you understand revenue, orders, inventory, "
            "cancellations, pricing and business growth. "
            "What would you like to explore?"
        )

    # SELLER PROFILE
    if intent == "profile":

        return (
            f"Here is the sample business information I have "
            f"for you, {seller_name}. "
            f"Seller ID: {seller.get('seller_id', 'Not provided')}. "
            f"Category: {seller.get('category', seller.get('business_category', 'Not provided'))}. "
            f"Location: {seller.get('location', seller.get('city', 'Not provided'))}. "
            f"Last month sales were {money(old['sales'])} "
            f"from {old['orders']} orders. "
            f"This month sales are {money(new['sales'])} "
            f"from {new['orders']} orders. "
            "I also have average selling price, cancellation rate "
            "and stock-out information. This is mock demo data, "
            "not a live Snapdeal account connection."
        )

    # LAST MONTH REVENUE
    if intent == "last_month_revenue":

        return (
            f"Last month, your recorded sales revenue was "
            f"{money(old['sales'])}. You received "
            f"{old['orders']} orders. Your average selling "
            f"price was {money(last_asp)}. Your cancellation "
            f"rate was {old['cancellation_rate']} percent, "
            f"and {old['out_of_stock_products']} products "
            "were out of stock."
        )

    # THIS MONTH REVENUE
    if intent == "this_month_revenue":

        return (
            f"This month, your recorded sales revenue is "
            f"{money(new['sales'])}. You received "
            f"{new['orders']} orders. Your average selling "
            f"price is {money(current_asp)}. Your cancellation "
            f"rate is {new['cancellation_rate']} percent, "
            f"and {new['out_of_stock_products']} products "
            "are out of stock."
        )

    # REVENUE OVERVIEW
    if intent == "revenue":

        return (
            f"Here is your revenue overview. Last month, "
            f"you recorded {money(old['sales'])} from "
            f"{old['orders']} orders. This month, you recorded "
            f"{money(new['sales'])} from {new['orders']} orders. "
            f"Your sales decreased by "
            f"{abs(a['changes']['sales_pct'])} percent. "
            f"Your average selling price remained at "
            f"{money(current_asp)}. Would you like me to "
            "explain why your revenue decreased?"
        )

    # REVENUE DIFFERENCE
    if intent == "revenue_difference":

        difference = a["changes"]["revenue_difference"]

        return (
            f"Compared with last month, your recorded sales "
            f"are lower by {money(difference)}. Last month "
            f"you recorded {money(old['sales'])}, while this "
            f"month you recorded {money(new['sales'])}. "
            "This is a sales difference, not a verified "
            "calculation of lost profit."
        )

    # AVERAGE ORDER VALUE
    if intent == "average_order_value":

        last_aov = (
            old["sales"] / old["orders"]
            if old["orders"] else 0
        )

        current_aov = (
            new["sales"] / new["orders"]
            if new["orders"] else 0
        )

        return (
            f"Your average sales per order were "
            f"{money(last_aov)} last month and "
            f"{money(current_aov)} this month. "
            "This is calculated by dividing total sales "
            "by total orders."
        )

    # ORDERS
    if intent == "orders":

        return (
            f"You received {old['orders']} orders last month "
            f"and {new['orders']} orders this month. "
            f"That is a decrease of "
            f"{abs(a['changes']['orders_pct'])} percent. "
            "We should investigate product availability, "
            "cancellations and listing conversion to understand "
            "the decline."
        )

    # INVENTORY
    if intent == "inventory":

        return (
            f"Your out-of-stock product count increased from "
            f"{old['out_of_stock_products']} last month to "
            f"{new['out_of_stock_products']} this month. "
            f"That is {a['changes']['stock_delta']} additional "
            "products unavailable. I recommend identifying "
            "your best-selling products and replenishing those "
            "first. Your dataset does not contain individual "
            "SKU details, so I cannot name a specific product."
        )

    # CANCELLATIONS
    if intent == "cancellations":

        return (
            f"Your cancellation rate increased from "
            f"{old['cancellation_rate']} percent to "
            f"{new['cancellation_rate']} percent. "
            f"That is an increase of "
            f"{a['changes']['cancellation_delta']} "
            "percentage points. I recommend reviewing "
            "cancelled orders by reason, such as stock mismatch, "
            "seller rejection, dispatch delay or customer "
            "cancellation. The exact reasons are not included "
            "in the sample dataset."
        )

    # PRICING
    if intent == "pricing":

        return (
            f"Your average selling price remained at "
            f"{money(last_asp)} last month and "
            f"{money(current_asp)} this month. "
            "The sample data does not show a price change. "
            "To evaluate competitiveness, compare similar "
            "products and their selling prices. I do not have "
            "competitor prices in this dataset."
        )

    # DISCOUNTS
    if intent == "discounts":

        return (
            "Discounts can attract buyers, but I would not "
            "recommend reducing prices without checking "
            "product costs and margins first. Compare the "
            "conversion of products with and without offers. "
            "Your dataset does not contain discount history "
            "or profit margins."
        )

    # PROFIT
    if intent == "profit":

        return (
            "I currently have your sales, orders, average "
            "selling price, cancellation rate and inventory "
            "figures. I do not have product costs, platform "
            "fees, shipping expenses or advertising costs. "
            "Therefore, I cannot calculate your actual net "
            "profit or profit margin."
        )

    # PRODUCT PERFORMANCE
    if intent == "product_performance":

        return (
            "I can see your overall sales and inventory "
            "performance, but the sample dataset does not "
            "contain individual product names, SKU-level "
            "sales or product conversion data. To identify "
            "your best-selling and worst-performing products, "
            "we need product-wise revenue, orders and stock data."
        )

    # VISIBILITY
    if intent == "visibility":

        return (
            "Your current dataset does not include product "
            "impressions, search rankings or product-page views, "
            "so I cannot confirm a visibility problem. "
            "I recommend checking impressions, clicks and "
            "conversion rates for your in-stock products."
        )

    # LISTING QUALITY
    if intent == "listing":

        return (
            "To improve your product listings, use clear "
            "high-quality images, accurate titles, complete "
            "product attributes and useful descriptions. "
            "Keep products in stock and monitor impressions, "
            "clicks and conversion rates. I do not have "
            "individual listing data to identify a specific "
            "product that needs editing."
        )

    # CUSTOMER BEHAVIOUR
    if intent == "customers":

        return (
            "Your current dataset contains aggregate sales "
            "and order counts, but not customer profiles, "
            "repeat purchases, customer feedback or browsing "
            "behaviour. I recommend tracking repeat purchase "
            "rates, customer feedback and product demand to "
            "understand your customer base."
        )

    # SEASONAL DEMAND
    if intent == "seasonal":

        return (
            "Seasonal demand planning can help you prepare "
            "inventory and promotions in advance. Review "
            "historical sales around festivals, identify "
            "high-demand products and replenish stock before "
            "demand increases. Your sample contains only two "
            "monthly periods, so it cannot establish a seasonal "
            "demand pattern."
        )

    # SALES DECLINE ANALYSIS
    if intent == "analysis":

        return (
            f"Let me explain what your numbers show. Your "
            f"sales decreased by {abs(a['changes']['sales_pct'])} "
            f"percent, from {money(old['sales'])} to "
            f"{money(new['sales'])}. Your orders declined "
            f"from {old['orders']} to {new['orders']}. "
            f"Your cancellation rate increased from "
            f"{old['cancellation_rate']} to "
            f"{new['cancellation_rate']} percent. "
            f"Out-of-stock products increased from "
            f"{old['out_of_stock_products']} to "
            f"{new['out_of_stock_products']}. "
            "These figures highlight inventory and "
            "cancellations as important areas to investigate. "
            "However, the dataset does not prove that either "
            "caused the entire sales decline. Would you like "
            "a recovery plan?"
        )

    # IMPACT
    if intent == "impact":

        return (
            "Yes, stock availability and cancellations can "
            "affect the number of orders that turn into "
            "completed sales. Your data shows 13 additional "
            "out-of-stock products and a cancellation-rate "
            "increase of 6 percentage points. These are "
            "important warning signals, but we need order-level "
            "data to quantify their individual revenue impact."
        )

    # BUSINESS STRENGTHS
    if intent == "strengths":

        return (
            f"One stable metric is your average selling price, "
            f"which remained at {money(current_asp)} across "
            "both periods. Your order volume has decreased, "
            "so improving order generation and product "
            "availability should be priorities. The sample "
            "dataset is limited, so I cannot identify all "
            "your business strengths."
        )

    # ACTION PLAN
    if intent == "action_plan":

        return (
            "Here is my recommended recovery plan. First, "
            "identify and replenish your highest-demand "
            "products among the 18 stock-outs. Second, "
            "investigate cancellation reasons and fix recurring "
            "operational issues. Third, improve product titles, "
            "images and descriptions. Fourth, review listing "
            "impressions, clicks and conversion rates. Finally, "
            "monitor sales and orders weekly to measure progress. "
            "Which area would you like to tackle first?"
        )

    # WEEKLY PLAN
    if intent == "weekly_plan":

        return (
            "Here is a practical weekly plan. On Monday, "
            "review stock-outs and identify priority products. "
            "On Tuesday, categorise cancellation reasons. "
            "On Wednesday, review product titles, images and "
            "descriptions. On Thursday, compare pricing with "
            "similar products. On Friday, review available "
            "traffic and conversion metrics. At the end of "
            "the week, compare sales, orders and cancellation "
            "rates. This is a suggested plan, not a schedule "
            "based on live marketplace data."
        )

    # SUMMARY
    if intent == "summary":

        return (
            f"Here is your business summary. Last month, "
            f"sales were {money(old['sales'])} from "
            f"{old['orders']} orders. This month, sales are "
            f"{money(new['sales'])} from {new['orders']} orders. "
            f"Sales decreased by "
            f"{abs(a['changes']['sales_pct'])} percent. "
            f"Cancellation rate increased from "
            f"{old['cancellation_rate']} to "
            f"{new['cancellation_rate']} percent. "
            f"Out-of-stock products increased from "
            f"{old['out_of_stock_products']} to "
            f"{new['out_of_stock_products']}. "
            "Your average selling price remained unchanged. "
            "I recommend prioritising inventory, cancellations "
            "and listing performance."
        )

    # GENERAL RESPONSE
    return (
        "I'm here to help you manage your seller business. "
        "You can ask about revenue, earnings, monthly sales, "
        "orders, inventory, cancellations, pricing, discounts, "
        "product visibility, customer behaviour or business "
        "growth. You can also ask for a recovery plan. "
        "What would you like to explore?"
    )


# =========================================================
# 8. GEMINI AI INTEGRATION
# =========================================================

def gemini_reply(
    message: str,
    history: List[Dict[str, str]]
) -> Optional[str]:

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return None

    try:

        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            os.getenv(
                "GEMINI_MODEL",
                "gemini-2.0-flash"
            ),

            system_instruction=(
                "You are Seller360, a friendly and professional "
                "voice-first Virtual Key Account Manager. "

                "Answer the seller's actual question directly. "
                "Use previous conversation context to understand "
                "follow-up questions. "

                "Last month sales: 200000 rupees. "
                "Last month orders: 400. "
                "Last month cancellation rate: 8 percent. "
                "Last month average selling price: 500 rupees. "
                "Last month out-of-stock products: 5. "

                "This month sales: 135000 rupees. "
                "This month orders: 270. "
                "This month cancellation rate: 14 percent. "
                "This month average selling price: 500 rupees. "
                "This month out-of-stock products: 18. "

                "Sales and orders decreased by 32.5 percent. "
                "Cancellation rate increased by 6 percentage "
                "points. Out-of-stock products increased by 13. "

                "Do not invent profit, SKU, customer, traffic, "
                "impression, competitor or cancellation-reason data. "

                "If information is missing, clearly say so and "
                "suggest what the seller should measure. "

                "Give practical recommendations. Keep answers "
                "concise and natural for voice conversations. "
                "Ask only one relevant follow-up question."
            )
        )

        past_history = history[-9:]

        # Avoid sending the current question twice
        if (
            past_history
            and past_history[-1].get("role") == "user"
            and past_history[-1].get("content", "").strip()
            == message.strip()
        ):
            past_history = past_history[:-1]

        convo = []

        for item in past_history:

            role = (
                "user"
                if item.get("role") == "user"
                else "model"
            )

            content = str(
                item.get("content", "")
            )[:1200]

            if content:
                convo.append({
                    "role": role,
                    "parts": [content]
                })

        chat = model.start_chat(history=convo)

        response = chat.send_message(message)

        answer = getattr(response, "text", None)

        if answer:
            return answer.strip()

        return None

    except Exception as error:

        print("Gemini error:", error)

        return None


# =========================================================
# 9. API ROUTES
# =========================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "Seller360 Virtual KAM"
    }


@app.get("/api/dashboard")
def dashboard():

    return analyze()


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    message = req.message.strip()

    a = analyze()

    if not message:

        return ChatResponse(
            reply="Please tell me what you would like to know.",
            insights=a["insights"],
            actions=a["actions"],
            mode="demo-rules"
        )

    intent = detect_intent(
        message,
        req.history
    )

    known_intents = [
        "greeting",
        "profile",
        "last_month_revenue",
        "this_month_revenue",
        "revenue",
        "revenue_difference",
        "average_order_value",
        "orders",
        "inventory",
        "cancellations",
        "pricing",
        "discounts",
        "profit",
        "product_performance",
        "visibility",
        "listing",
        "customers",
        "seasonal",
        "analysis",
        "impact",
        "strengths",
        "action_plan",
        "weekly_plan",
        "summary"
    ]

    if intent in known_intents:

        answer = fallback_reply(
            message,
            req.history
        )

        mode = "demo-rules"

    else:

        answer = gemini_reply(
            message,
            req.history
        )

        mode = "gemini" if answer else "demo-rules"

        if not answer:

            answer = fallback_reply(
                message,
                req.history
            )

    return ChatResponse(
        reply=answer,
        insights=a["insights"],
        actions=a["actions"],
        mode=mode
    )


@app.get("/api/summary")
def summary():

    a = analyze()

    old = DATA["periods"]["last_month"]
    new = DATA["periods"]["this_month"]

    return {
        "summary": (
            f"Sales declined by "
            f"{abs(a['changes']['sales_pct'])} percent "
            f"from {money(old['sales'])} to "
            f"{money(new['sales'])}. Orders decreased from "
            f"{old['orders']} to {new['orders']}. "
            f"Cancellation rate increased from "
            f"{old['cancellation_rate']} to "
            f"{new['cancellation_rate']} percent. "
            f"Out-of-stock products increased from "
            f"{old['out_of_stock_products']} to "
            f"{new['out_of_stock_products']}. "
            f"Average selling price remained at "
            f"{money(get_asp(new))}. "
            "Prioritise replenishing high-demand products, "
            "investigating cancellation reasons and reviewing "
            "listing visibility and conversion. "
            "The sample data does not confirm exact root causes."
        ),

        "actions": a["actions"],
        "assumptions": a["assumptions"]
    }
