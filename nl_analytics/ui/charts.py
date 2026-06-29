import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

def auto_chart(df: pd.DataFrame, question: str):
    """
    Analyzes the DataFrame shape, data types, and user question to construct
    the most appropriate Plotly Express chart.
    
    Returns:
        plotly.graph_objects.Figure or None: A Plotly figure if a chart is suitable,
                                             otherwise None (triggers standard table rendering).
    """
    if df is None or df.empty:
        return None
        
    num_rows, num_cols = df.shape
    title = f"Insight: {question}"
    
    # 1. 1 Row & 1 Column -> Plotly Indicator (Metric Card)
    if num_rows == 1 and num_cols == 1:
        val = df.iloc[0, 0]
        col = df.columns[0]
        try:
            val_num = float(val)
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                mode="number",
                value=val_num,
                title={"text": f"<b>{col}</b>", "font": {"size": 18, "color": "#ff6b81"}},
                number={"font": {"size": 52, "color": "#ff2a4b"}, "valueformat": ",.2f"}
            ))
            fig.update_layout(
                title={"text": title, "font": {"size": 14, "color": "#ffffff"}},
                height=250,
                margin=dict(l=20, r=20, t=50, b=20),
                template="plotly_dark",
                paper_bgcolor="#121318",
                plot_bgcolor="#0b0c10"
            )
            return fig
        except Exception:
            # Not a numeric value, fall back to table view
            return None

    # Identify column data types
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    date_keywords = ['date', 'month', 'year', 'quarter', 'day']
    date_cols = [col for col in df.columns if any(kw in col.lower() for kw in date_keywords)]
    
    # Custom neon red sequence
    red_sequence = ['#ff2a4b', '#ff6b81', '#ff99a8', '#cc0022', '#800016']

    def apply_dark_theme(figure):
        figure.update_layout(
            template="plotly_dark",
            paper_bgcolor="#121318",
            plot_bgcolor="#0b0c10",
            font=dict(color="#ffffff", family="Outfit")
        )
        return figure

    # 2. If df contains date/month columns and numeric columns -> Line Chart (Trend)
    if date_cols and numeric_cols:
        df_sorted = df.sort_values(by=date_cols[0])
        fig = px.line(
            df_sorted,
            x=date_cols[0],
            y=numeric_cols[0],
            title=title,
            height=450,
            color_discrete_sequence=['#ff2a4b'],
            hover_data=df.columns.tolist()
        )
        fig.update_layout(hovermode="x unified")
        return apply_dark_theme(fig)

    # 3. If question is about sharing/proportions -> Pie Chart
    question_lower = question.lower()
    has_share_word = any(kw in question_lower for kw in ["share", "percent", "percentage", "proportion"])
    has_share_col = any("share" in str(col).lower() or "percent" in str(col).lower() for col in df.columns)
    if (has_share_word or has_share_col) and len(numeric_cols) >= 1 and num_cols >= 2:
        cat_cols = [col for col in df.columns if col not in numeric_cols]
        names_col = cat_cols[0] if cat_cols else df.columns[0]
        fig = px.pie(
            df,
            names=names_col,
            values=numeric_cols[0],
            title=title,
            height=450,
            color_discrete_sequence=red_sequence
        )
        return apply_dark_theme(fig)

    # 4. If there are exactly two numeric columns -> Scatter Chart
    if len(numeric_cols) >= 2 and num_cols == 2:
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=title,
            height=450,
            color_discrete_sequence=['#ff2a4b'],
            hover_data=df.columns.tolist()
        )
        return apply_dark_theme(fig)

    # 5. Category + number -> Bar Chart
    if num_cols == 2 and len(numeric_cols) == 1:
        cat_cols = [col for col in df.columns if col not in numeric_cols]
        if cat_cols:
            fig = px.bar(
                df,
                x=cat_cols[0],
                y=numeric_cols[0],
                title=title,
                height=450,
                color_discrete_sequence=['#ff2a4b'],
                hover_data=df.columns.tolist()
            )
            return apply_dark_theme(fig)

    # 6. More than 5 columns -> Styled Table (returns None to render st.dataframe)
    if num_cols > 5:
        return None

    # 7. Default fallback: Bar Chart (if numeric columns are present)
    if numeric_cols:
        x_col = df.columns[0] if df.columns[0] not in numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        fig = px.bar(
            df,
            x=x_col,
            y=numeric_cols[0],
            title=title,
            height=450,
            color_discrete_sequence=['#ff2a4b'],
            hover_data=df.columns.tolist()
        )
        return apply_dark_theme(fig)

    # Default fallback: No chart, show tabular dataframe
    return None
