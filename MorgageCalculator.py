import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_mortgage(principal, rate, years):
    """Standard mortgage payment calculation."""
    r_monthly = rate / 12
    n_months = years * 12
    payment = (principal * r_monthly) / (1 - (1 + r_monthly)**(-n_months))
    return payment

def calculate_payoff_time(principal, rate, payment):
    """Calculates how many months remain based on a specific payment size."""
    r_monthly = rate / 12
    # Ensure payment is large enough to cover at least the interest
    if payment <= principal * r_monthly:
        return float('inf') # Loan will never be paid off
        
    n_months = -np.log(1 - (principal * r_monthly) / payment) / np.log(1 + r_monthly)
    return n_months


def calculate_buyability(principal, rate, years, take_home_monthly_pay):
    """Determines whether the mortgage payment fits within 28% of take-home pay."""
    monthly_payment = calculate_mortgage(principal, rate, years)
    affordable_payment = take_home_monthly_pay * 0.28
    required_take_home_pay = monthly_payment / 0.28 if monthly_payment > 0 else 0
    return {
        "monthly_payment": monthly_payment,
        "affordable_payment": affordable_payment,
        "required_take_home_pay": required_take_home_pay,
        "is_affordable": monthly_payment <= affordable_payment,
        "shortfall": max(0.0, monthly_payment - affordable_payment)
    }


def calculate_max_affordable_principal(rate, years, take_home_monthly_pay):
    """Calculates the maximum loan principal affordable if P&I is capped at 28% of take-home pay."""
    target_payment = take_home_monthly_pay * 0.28
    r_monthly = rate / 12
    n_months = years * 12
    if target_payment <= 0:
        return 0.0
    if r_monthly == 0:
        return target_payment * n_months
    principal = target_payment * (1 - (1 + r_monthly) ** -n_months) / r_monthly
    return principal

st.title("My Mortgage Analyzer")

# Pre-filled with Chase Pre-Approval Data
principal = st.number_input("Loan Amount ($)", value=136000.00)
rate = st.number_input("Interest Rate (%)", value=0.06125)
years = st.number_input("Loan Term (Years)", value=30)

base_payment = calculate_mortgage(principal, rate, years)
st.write(f"### Standard Monthly Payment (P&I): **${base_payment:.2f}**")

# Buy-ability analysis using 28% of take-home pay
monthly_take_home = st.number_input("Take-Home Monthly Pay ($)", value=5833.33)

buyability = calculate_buyability(principal, rate, years, monthly_take_home)
max_principal = calculate_max_affordable_principal(rate, years, monthly_take_home)

if buyability["is_affordable"]:
    message = (
        f"Your P&I payment of ${buyability['monthly_payment']:.2f} is within 28% of your take-home pay ${buyability['affordable_payment']:.2f}"
    )
    st.success(message)
else:
    message = (
        f"Your payment of ${buyability['monthly_payment']:.2f} exceeds 28% of take-home pay by "
        f"${buyability['shortfall']:.2f}. You would need at least "
        f"${buyability['required_take_home_pay']:.2f} take-home pay per month to keep P&I at 28%."
    )
    st.warning(message)

st.write(f"### Maximum Affordable Loan Principal: **${max_principal:,.2f}** if P&I is capped at 28% of take-home pay.")
st.divider()

st.subheader("Scenario 1: Extra Monthly Payments")
extra_monthly = st.number_input("Extra Principal Payment per Month ($)", value=100.00)

if extra_monthly > 0:
    new_total_payment = base_payment + extra_monthly
    new_months = calculate_payoff_time(principal, rate, new_total_payment)
    new_years = new_months / 12
    
    time_saved = years - new_years
    st.success(f"By paying an extra ${extra_monthly:.2f}/mo, you will pay off the loan in **{new_years:.1f} years** (saving {time_saved:.1f} years!).")

st.subheader("Scenario 2: One-Time Lump Sum (No Recast)")
lump_sum = st.number_input("One-time Lump Sum Payment ($)", value=5000.00)

if lump_sum > 0:
    new_principal = principal - lump_sum
    # Payment stays the same, so we calculate the new time based on the base_payment
    new_months_lump = calculate_payoff_time(new_principal, rate, base_payment)
    new_years_lump = new_months_lump / 12
    
    time_saved_lump = years - new_years_lump
    st.info(f"A one-time payment of ${lump_sum:.2f} cuts the mortgage down to **{new_years_lump:.1f} years** (saving {time_saved_lump:.1f} years!). Your payment stays ${base_payment:.2f}.")

# ============================================================================
# BUDGETING SECTION
# ============================================================================
st.divider()
st.header("💰 Monthly Budget Analysis")

# Create two columns for budget inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("Income & Deductions")
    annual_salary = st.number_input("Annual Gross Salary ($)", value=70000.00, min_value=0.0, step=1000.0)
    income_tax_rate = st.number_input("Income Tax Rate (%)", value=22.0, min_value=0.0, max_value=100.0, step=0.5)
    tithing_rate = st.number_input("Tithing (% of Take-Home)", value=10.0, min_value=0.0, max_value=100.0, step=0.5)
    retirement_401k_rate = st.number_input("401k Contribution (% of Gross)", value=5.0, min_value=0.0, max_value=100.0, step=0.5)
    roth_ira_monthly = st.number_input("Roth IRA Monthly ($)", value=583.00, min_value=0.0, step=50.0)

with col2:
    st.subheader("Housing & Living Expenses")
    utilities_monthly = st.number_input("Utilities Monthly ($)", value=500.00, min_value=0.0, step=50.0)
    property_tax_insurance = st.number_input("Property Tax & Insurance Monthly ($)", value=200.00, min_value=0.0, step=25.0)

# Calculate monthly take-home with pre-tax 401k removed before tax calculation
monthly_gross = annual_salary / 12
monthly_401k = monthly_gross * (retirement_401k_rate / 100)
monthly_taxable_income = monthly_gross - monthly_401k
monthly_income_tax = monthly_taxable_income * (income_tax_rate / 100)
monthly_take_home_after_deductions = monthly_gross - monthly_401k - monthly_income_tax

# Calculate deductions
monthly_tithing = (monthly_take_home_after_deductions + monthly_401k )* (tithing_rate / 100) 

# Mortgage payment (Principal & Interest)
mortgage_pi = base_payment
total_house_payment = mortgage_pi + property_tax_insurance

# Calculate remaining for living expenses
living_expenses = monthly_take_home_after_deductions - monthly_tithing - roth_ira_monthly - utilities_monthly - total_house_payment

# Create budget display
st.subheader("Monthly Budget Breakdown")

col_pie, col_table = st.columns([1, 1])

with col_pie:
    # Create pie chart data
    budget_categories = [
        "Income Tax",
        "401k (Pre-tax)",
        "Tithing",
        "Roth IRA",
        "Utilities",
        "Mortgage (P&I + Tax/Ins)",
        "Living Expenses\n(Food, Gas, Fun, Maintenance)"
    ]
    
    budget_amounts = [
        monthly_income_tax,
        monthly_401k,
        monthly_tithing,
        roth_ira_monthly,
        utilities_monthly,
        total_house_payment,
        max(0, living_expenses)  # Ensure non-negative for display
    ]
    
    # Filter out zero values for better pie chart visualization
    non_zero_amounts = []
    non_zero_labels = []
    for label, amount in zip(budget_categories, budget_amounts):
        if amount > 0:
            non_zero_amounts.append(amount)
            non_zero_labels.append(label)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.Set3(range(len(non_zero_amounts)))
    wedges, texts, autotexts = ax.pie(
        non_zero_amounts,
        labels=non_zero_labels,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )
    
    # Enhance text readability
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(9)
        autotext.set_weight('bold')
    
    plt.title("Monthly Budget Distribution", fontsize=14, fontweight='bold')
    st.pyplot(fig)

with col_table:
    # Create detailed budget table
    st.write("### Budget Details")
    
    budget_data = {
        "Category": [
            "Gross Monthly Income",
            "Income Tax",
            "401k (Pre-tax)",
            "Take-Home (After Tax & 401k)",
            "",
            "Tithing (10% of Take-Home)",
            "Roth IRA",
            "Utilities",
            "Mortgage (P&I)",
            "Property Tax & Insurance",
            "Total House Payment",
            "",
            "Living Expenses*"
        ],
        "Amount": [
            f"${monthly_gross:,.2f}",
            f"-${monthly_income_tax:,.2f}",
            f"-${monthly_401k:,.2f}",
            f"${monthly_take_home_after_deductions:,.2f}",
            "",
            f"-${monthly_tithing:,.2f}",
            f"-${roth_ira_monthly:,.2f}",
            f"-${utilities_monthly:,.2f}",
            f"-${mortgage_pi:,.2f}",
            f"-${property_tax_insurance:,.2f}",
            f"-${total_house_payment:,.2f}",
            "",
            f"${max(0, living_expenses):,.2f}"
        ]
    }
    
    df_budget = pd.DataFrame(budget_data)
    # Remove index and display
    st.dataframe(df_budget, use_container_width=True, hide_index=True)
    
    st.caption("*Living Expenses for Food, Gas, Fun, Maintenance, and other discretionary spending")

# Summary metrics
st.divider()
col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)

with col_summary1:
    st.metric("Monthly Gross", f"${monthly_gross:,.2f}")

with col_summary2:
    st.metric("Monthly Take-Home", f"${monthly_take_home_after_deductions:,.2f}")

with col_summary3:
    st.metric("Total House Payment", f"${total_house_payment:,.2f}")
    
with col_summary4:
    remaining_pct = (max(0, living_expenses) / monthly_take_home_after_deductions * 100) if monthly_take_home_after_deductions > 0 else 0
    st.metric("Living Expenses", f"${max(0, living_expenses):,.2f}", f"{remaining_pct:.1f}% of take-home")

# Budget health warning
if living_expenses < 0:
    st.error("⚠️ **Budget Alert**: Monthly expenses exceed take-home income! Adjust inputs to balance your budget.")
elif living_expenses < 500:
    st.warning("⚠️ **Tight Budget**: Limited funds remaining for living expenses. Consider reducing other expenses or increasing income.")
elif living_expenses >= 2000:
    st.success("✅ **Healthy Budget**: Good balance with sufficient living expense allocation.")
