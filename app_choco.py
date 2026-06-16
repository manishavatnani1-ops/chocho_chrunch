import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="ChocoCrunch Data Analytics Dashboard",
    page_icon="🍫",
    layout="wide"
)

# ----------------------------------------------------
# 1. DATABASE CONNECTION & INITIALIZATION
# ----------------------------------------------------
def get_db_connection(use_db=True):
    """Establishes connection to MySQL server."""
    config = {
        "host": "localhost",
        "user": "root",
        "password": "root",  # Update with your password
        "autocommit": True
    }
    if use_db:
        config["database"] = "ChocoCrunch"
    return mysql.connector.connect(**config)

@st.cache_data
def run_query(query):
    """Helper function to execute a query and return a Pandas DataFrame."""
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

# Initialize Database Structure if running for the first time
def init_db():
    try:
        conn = get_db_connection(use_db=False)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ChocoCrunch")
        cursor.execute("USE ChocoCrunch")
        conn.close()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")

# Run DB initialization hidden in background
init_db()


# ----------------------------------------------------
# 2. APP HEADER & SIDEBAR NAVIGATION
# ----------------------------------------------------
st.title("🍫 ChocoCrunch Advanced EDA & SQL Metrics Dashboard")
st.markdown("Interactive analysis portal powered by MySQL database structured metrics.")
st.write("---")

# Sidebar navigation - FIXED: Values here now perfectly match the routing logic below
sidebar_options = [
    "📊 Exploratory Data Analysis (EDA)", 
    "📑 product_info", 
    "📑 nutrient_info", 
    "📑 Derived Metrics", 
    "🔗 Relational Join Queries"
]

st.sidebar.image("https://img.icons8.com/fluent/96/000000/chocolate-bar.png", width=80)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", sidebar_options)


# ----------------------------------------------------
# PAGE 1: EDA OVERVIEW
# ----------------------------------------------------
if page == "📊 Exploratory Data Analysis (EDA)":
    st.header("🔍 Overview & Quick Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_products = run_query("SELECT COUNT(*) as count FROM product_info")
        if not total_products.empty and "Error" not in total_products.columns:
            st.metric("Total Products Captured", total_products["count"][0])
            
    with col2:
        # FIXED: Changed 'brand' to 'brands' to match schema continuity
        total_brands = run_query("SELECT COUNT(DISTINCT brands) as count FROM product_info")
        if not total_brands.empty and "Error" not in total_brands.columns:
            st.metric("Unique Brands Available", total_brands["count"][0])
            
    with col3:
        # Note: Ensure a 'derived_metrics' view/table exists in your database for this to execute cleanly
        ultra_processed = run_query("SELECT COUNT(*) as count FROM derived_metrics WHERE calorie_category = 'Ultra-Processed' OR sugar_to_carb_ratio > 0.7")
        if not ultra_processed.empty and "Error" not in ultra_processed.columns:
            st.metric("High Concern Metrics Count", ultra_processed["count"][0])

    st.subheader("💡 Dataset Sample Preview")
    sample_df = run_query("SELECT * FROM product_info LIMIT 10")
    st.dataframe(sample_df, use_container_width=True)


# ----------------------------------------------------
# PAGE 2: PRODUCT INFO METRICS
# ----------------------------------------------------
elif page == "📑 product_info":
    st.header("📦 Product Info Metrics")
    
    tab1, tab2, tab3 = st.tabs(["Brand Summaries", "Product Outliers", "Prefix Filter"])
    
    with tab1:
        st.subheader("Count Products Per Brand & Unique Brand Status")
        query_brand_counts = """
        SELECT brands, COUNT(*) as total_products, COUNT(DISTINCT product_name) as unique_products
        FROM product_info
        GROUP BY brands
        ORDER BY total_products DESC
        """
        df_brands = run_query(query_brand_counts)
        st.dataframe(df_brands, use_container_width=True)
        
        # Plot top 5
        st.subheader("🔥 Top 5 Brands by Product Count")
        df_top5 = df_brands.head(5)
        if not df_top5.empty and "Error" not in df_top5.columns:
            fig = px.bar(df_top5, x="brands", y="total_products", color="brands", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🕵️ Products with Missing Product Name")
        df_missing = run_query("SELECT * FROM product_info WHERE product_name IS NULL OR product_name = ''")
        st.dataframe(df_missing, use_container_width=True)
        
        st.subheader("📈 Total Unique Brands Summary Count")
        # FIXED: Changed 'brand' to 'brands'
        df_uniq_count = run_query("SELECT COUNT(DISTINCT brands) as total_unique_brands FROM product_info")
        st.dataframe(df_uniq_count)

    with tab3:
        st.subheader("🔢 Products with Code Starting with '3'")
        df_code3 = run_query("SELECT * FROM product_info WHERE code LIKE '3%'")
        st.dataframe(df_code3, use_container_width=True)


# ----------------------------------------------------
# PAGE 3: NUTRIENT INFO METRICS
# ----------------------------------------------------
elif page == "📑 nutrient_info":
    st.header("🥗 Nutrient Info Diagnostics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚀 Top 10 Products with Highest Energy (kcal)")
        query_top_kcal = "SELECT code, `energy-kcal_value` FROM nutrient_info ORDER BY `energy-kcal_value` DESC LIMIT 10"
        df_kcal = run_query(query_top_kcal)
        st.dataframe(df_kcal, use_container_width=True)
        
    with col2:
        st.subheader("🥛 Average Sugars Value per Nova-Group")
        query_nova = "SELECT `nova-group`, AVG(sugars_value) as avg_sugar FROM nutrient_info GROUP BY `nova-group` ORDER BY `nova-group`"
        df_nova = run_query(query_nova)
        st.dataframe(df_nova, use_container_width=True)
        if not df_nova.empty and "Error" not in df_nova.columns:
            fig_nova = px.line(df_nova, x="nova-group", y="avg_sugar", markers=True)
            st.plotly_chart(fig_nova, use_container_width=True)

    st.write("---")
    st.subheader("📊 General Nutritional Distributions & Filters")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Fat Value > 20g**")
        df_fat = run_query("SELECT COUNT(*) as count FROM nutrient_info WHERE fat_value > 20")
        st.metric("Total Count", df_fat["count"][0] if not df_fat.empty and "Error" not in df_fat.columns else 0)
        
    with c2:
        st.markdown("**Sodium Value > 1g**")
        df_sodium = run_query("SELECT COUNT(*) as count FROM nutrient_info WHERE sodium_value > 1")
        st.metric("Total Count", df_sodium["count"][0] if not df_sodium.empty and "Error" not in df_sodium.columns else 0)
        
    with c3:
        st.markdown("**Energy Value > 500 kcal**")
        df_high_energy = run_query("SELECT COUNT(*) as count FROM nutrient_info WHERE `energy-kcal_value` > 500")
        st.metric("Total Count", df_high_energy["count"][0] if not df_high_energy.empty and "Error" not in df_high_energy.columns else 0)
        
    st.write(" ")
    col_avg1, col_avg2 = st.columns(2)
    with col_avg1:
        st.subheader("📉 Average Carbohydrates per Product")
        st.dataframe(run_query("SELECT AVG(carbohydrates_value) as global_avg_carbs FROM nutrient_info"))
        
    with col_avg2:
        st.subheader("🌱 Non-Zero Fruits/Vegetables/Nuts Content")
        st.dataframe(run_query("SELECT COUNT(*) as non_zero_count FROM nutrient_info WHERE `fruits-vegetables-nuts_value` > 0"))


# ----------------------------------------------------
# PAGE 4: DERIVED METRICS
# ----------------------------------------------------
elif page == "📑 Derived Metrics":  # FIXED: Target match string explicitly matched
    st.header("⚡ Derived Metrics & Classification")
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.subheader("📦 Product Count per Calorie Category")
        query_cal_cat = """
        SELECT 
            CASE 
                WHEN `energy-kcal_value` > 500 THEN 'High Calorie'
                WHEN `energy-kcal_value` BETWEEN 200 AND 500 THEN 'Medium Calorie'
                ELSE 'Low Calorie'
            END AS calorie_category,
            COUNT(*) as product_count 
        FROM nutrient_info 
        GROUP BY calorie_category
        """
        df_cal_cat = run_query(query_cal_cat)
        if df_cal_cat is not None and not df_cal_cat.empty and "Error" not in df_cal_cat.columns:
            st.dataframe(df_cal_cat, use_container_width=True)
            fig_pie = px.pie(df_cal_cat, names="calorie_category", values="product_count", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with col_m2:
        st.subheader("📊 Average Sugar to Carb Ratio per Calorie Category")
        query_ratio = """
        SELECT 
            CASE 
                WHEN `energy-kcal_value` > 500 THEN 'High Calorie'
                WHEN `energy-kcal_value` BETWEEN 200 AND 500 THEN 'Medium Calorie'
                ELSE 'Low Calorie'
            END AS calorie_category, 
            AVG(sugars_value / NULLIF(carbohydrates_value, 0)) as avg_ratio 
        FROM nutrient_info 
        GROUP BY calorie_category
        """
        df_ratio = run_query(query_ratio)
        if df_ratio is not None:
            st.dataframe(df_ratio, use_container_width=True)
            
    st.write("---")
    st.subheader("🔍 Focused Segments & Threshold Outliers")
    t1, t2, t3 = st.tabs(["High Sugar/Calorie Flags", "Ultra-Processed", "Sugar-Carb Outliers"])
    
    with t1:
        st.markdown("**Count of High Sugar Products (>15g):**")
        st.dataframe(run_query("SELECT COUNT(*) as count FROM nutrient_info WHERE sugars_value > 15"))
        
        st.markdown("**Average Sugar-to-Carb Ratio for High Calorie Products:**")
        st.dataframe(run_query("SELECT AVG(sugars_value / NULLIF(carbohydrates_value, 0)) as avg_ratio FROM nutrient_info WHERE `energy-kcal_value` > 500"))
        
        st.markdown("**Products both High Calorie & High Sugar:**")
        st.dataframe(run_query("SELECT code, `energy-kcal_value`, sugars_value FROM nutrient_info WHERE `energy-kcal_value` > 500 AND sugars_value > 15 LIMIT 50"))
        
    with t2:
        st.markdown("**Number of Products marked as Ultra-Processed (NOVA 4):**")
        st.dataframe(run_query("SELECT COUNT(*) as ultra_processed_count FROM nutrient_info WHERE `nova-group` = 4"))
        
    with t3:
        st.markdown("**Products with Sugar to Carb Ratio > 0.7:**")
        st.dataframe(run_query("SELECT code, sugars_value, carbohydrates_value, (sugars_value / carbohydrates_value) as sugar_to_carb_ratio FROM nutrient_info WHERE carbohydrates_value > 0 AND (sugars_value / carbohydrates_value) > 0.7"), use_container_width=True)


# ----------------------------------------------------
# PAGE 5: JOIN QUERIES
# ----------------------------------------------------
elif page == "🔗 Relational Join Queries":  # FIXED: Target match string explicitly matched
    st.header("🔗 Cross-Table Relational Join Queries")
    
    st.subheader("🏆 Top 5 Brands with most High Calorie Products")
    q_join1 = """
    SELECT p.brands, COUNT(*) as high_calorie_count 
    FROM product_info p 
    JOIN nutrient_info n ON p.code = n.code 
    WHERE n.`energy-kcal_value` > 500 AND p.brands IS NOT NULL AND p.brands != '' 
    GROUP BY p.brands 
    ORDER BY high_calorie_count DESC 
    LIMIT 5
    """
    df_join1 = run_query(q_join1)
    if df_join1 is not None:
        st.dataframe(df_join1, use_container_width=True)
        
    st.subheader("⚡ Average energy-kcal_value for each Calorie Category")
    q_join2 = """
    SELECT 
        CASE 
            WHEN n.`energy-kcal_value` > 500 THEN 'High Calorie'
            WHEN n.`energy-kcal_value` BETWEEN 200 AND 500 THEN 'Medium Calorie'
            ELSE 'Low Calorie'
        END AS calorie_category,
        AVG(n.`energy-kcal_value`) as avg_energy
    FROM nutrient_info n
    GROUP BY calorie_category
    """
    df_join2 = run_query(q_join2)
    if df_join2 is not None:
        st.dataframe(df_join2, use_container_width=True)
        
    st.subheader("🏭 Count of Ultra-Processed Products per Brand")
    q_join3 = """
    SELECT p.brands, COUNT(*) as up_count 
    FROM product_info p 
    JOIN nutrient_info n ON p.code = n.code 
    WHERE n.`nova-group` = 4 AND p.brands IS NOT NULL AND p.brands != '' 
    GROUP BY p.brands 
    ORDER BY up_count DESC
    """
    df_join3 = run_query(q_join3)
    if df_join3 is not None:
        st.dataframe(df_join3, use_container_width=True)
        
    st.subheader("🌶️ Products with High Sugar and High Calorie alongside Brand mapping")
    q_join4 = """
    SELECT p.code, p.product_name, p.brands, n.`energy-kcal_value`, n.sugars_value 
    FROM product_info p 
    JOIN nutrient_info n ON p.code = n.code 
    WHERE n.`energy-kcal_value` > 500 AND n.sugars_value > 15
    """
    df_join4 = run_query(q_join4)
    if df_join4 is not None:
        st.dataframe(df_join4, use_container_width=True)
        
    st.subheader("🥣 Average Sugar Content per Brand for Ultra-Processed Products")
    q_join5 = """
    SELECT p.brands, AVG(n.sugars_value) as avg_sugar 
    FROM product_info p 
    JOIN nutrient_info n ON p.code = n.code 
    WHERE n.`nova-group` = 4 AND p.brands IS NOT NULL AND p.brands != '' 
    GROUP BY p.brands 
    ORDER BY avg_sugar DESC
    """
    df_join5 = run_query(q_join5)
    if df_join5 is not None:
        st.dataframe(df_join5, use_container_width=True)

    st.subheader("🌱 Number of Products with Fruits/Vegetables/Nuts Content in each Calorie Category")
    q_join6 = """
    SELECT 
        CASE 
            WHEN n.`energy-kcal_value` > 500 THEN 'High Calorie'
            WHEN n.`energy-kcal_value` BETWEEN 200 AND 500 THEN 'Medium Calorie'
            ELSE 'Low Calorie'
        END AS calorie_category,
        COUNT(*) as product_count
    FROM nutrient_info n
    WHERE n.`fruits-vegetables-nuts_value` > 0
    GROUP BY calorie_category
    """
    df_join6 = run_query(q_join6)
    if df_join6 is not None:
        st.dataframe(df_join6, use_container_width=True)

    st.subheader("🎯 Top 5 Products by Sugar-to-Carb Ratio with Calorie and Sugar Classifications")
    q_join7 = """
    SELECT 
        p.product_name, 
        p.brands, 
        ROUND((n.sugars_value / NULLIF(n.carbohydrates_value, 0)), 4) AS sugar_to_carb_ratio,
        CASE 
            WHEN n.`energy-kcal_value` > 500 THEN 'High Calorie'
            ELSE 'Normal Calorie'
        END AS calorie_category,
        CASE 
            WHEN n.sugars_value > 15 THEN 'High Sugar'
            ELSE 'Normal Sugar'
        END AS sugar_category
    FROM product_info p
    JOIN nutrient_info n ON p.code = n.code
    WHERE n.carbohydrates_value > 0
    ORDER BY sugar_to_carb_ratio DESC
    LIMIT 5
    """
    df_join7 = run_query(q_join7)
    if df_join7 is not None:
        st.dataframe(df_join7, use_container_width=True)