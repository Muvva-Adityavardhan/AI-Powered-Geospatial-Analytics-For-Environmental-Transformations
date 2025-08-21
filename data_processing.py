# data_processing.py
"""
Functions for generating reports and Plotly visualizations.
"""
import os
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import CORPUS_FOLDER, state_corpus_files, MISTRAL_API_URL, MISTRAL_API_KEY, GEMINI_API_KEY
from llm_services import call_mistral_saba, call_gemini


def generate_report(query, detected_states, year_dict, checkout_corpus_data, mistral_values):
    report = call_gemini(GEMINI_API_KEY, checkout_corpus_data, query, detected_states, mistral_values)
    return report

def generate_visualization(mistral_values, states, year_dict, query, requested_metrics):
    figures = []
    print(f"Initial Mistral Values: {mistral_values}")
    print(f"States: {states}")
    print(f"Year Dict: {year_dict}")
    print(f"Query: {query}")
    print(f"Requested Metrics: {requested_metrics}")

    data_by_state_year = {}
    for state in states:
        years = year_dict.get(state, ["2024"])
        if not isinstance(years, list):
            years = [years]
        years = sorted(set(str(y) for y in years if 2015 <= int(y) <= 2024))
        data_by_state_year[state] = {year: [0.0] * len(requested_metrics) for year in years}

    pattern = r"(?:(\d{4})\s+([A-Za-z\s]+)\n)?-?\s*(?:DynamicWorld\s+)?(\w+)\s*:\s*(\d+\.\d+)"
    matches = re.findall(pattern, mistral_values)
    print(f"Parsed Matches: {matches}")

    current_state = None
    current_year = None
    for year, state_name, metric, value in matches:
        state_name = state_name.strip() if state_name else None
        if state_name and year:
            current_state = next((s for s in states if s.lower() == state_name.lower()), None)
            current_year = year
        if current_state and current_year and metric in requested_metrics and current_year in data_by_state_year[current_state]:
            idx = requested_metrics.index(metric)
            try:
                data_by_state_year[current_state][current_year][idx] = float(value)
            except ValueError:
                print(f"Invalid value for {metric} in {current_state} {current_year}: {value}")
    print(f"Initial Data by State Year: {data_by_state_year}")

    checkout_corpus_data = ""
    for state in states:
        corpus_file_path = os.path.join(CORPUS_FOLDER, state_corpus_files[state])
        if os.path.exists(corpus_file_path):
            with open(corpus_file_path, "r", encoding="utf-8") as f:
                checkout_corpus_data += f"\n--- {state} ---\n" + f.read()

    for state in states:
        years = year_dict.get(state, ["2024"])
        years = sorted(set(str(y) for y in years if 2015 <= int(y) <= 2024))
        
        for year in years:
            if not any(data_by_state_year[state][year]):
                specific_query = f"Environmental data for {', '.join(requested_metrics)} in {state} {year}"
                mistral_response = call_mistral_saba(MISTRAL_API_URL, MISTRAL_API_KEY,
                                                     checkout_corpus_data, specific_query,
                                                     [state], requested_metrics)
                print(f"Mistral Response for {state} {year}: {mistral_response}")
                matches = re.findall(pattern, mistral_response)
                current_state = state
                current_year = year
                for _, _, metric, value in matches:
                    if metric in requested_metrics:
                        idx = requested_metrics.index(metric)
                        try:
                            data_by_state_year[current_state][current_year][idx] = float(value)
                        except ValueError:
                            print(f"Invalid value for {metric} in {current_state} {current_year}: {value}")
                print(f"Updated Data for {state} {year}: {data_by_state_year[state][year]}")

    if "land cover" in query.lower():
        for state in data_by_state_year:
            for year in data_by_state_year[state]:
                values = data_by_state_year[state][year]
                total = sum(values)
                if total > 0 and abs(total - 1.0) > 0.01:
                    print(f"Normalizing land cover data for {state} {year}: sum={total}")
                    data_by_state_year[state][year] = [v / total for v in values]
                print(f"Normalized Data for {state} {year}: {data_by_state_year[state][year]}")

    if len(states) > 1 and "compare" in query.lower() and "land cover" not in query.lower() and len(requested_metrics) > 1:
        metrics = [(year, metric, float(value), state)
                   for year, state_name, metric, value in matches
                   if metric in requested_metrics and state_name.strip() in states]
        print(f"Bar Chart Matches: {metrics}")
        if metrics:
            df = pd.DataFrame(metrics, columns=["Year", "Metric", "Value", "State"])
            print(f"Bar Chart DataFrame: {df}")
            if not df.empty:
                pivot_df = df.pivot_table(index=["State", "Year"], columns="Metric",
                                          values="Value", aggfunc="first").reset_index().fillna(0.0)
                pivot_df['State_Year'] = pivot_df['State'] + ' (' + pivot_df['Year'] + ')'
                print(f"Pivot DataFrame: {pivot_df}")

                fig = go.Figure()
                for metric in requested_metrics:
                    if metric in pivot_df.columns:
                        fig.add_trace(go.Bar(
                            x=pivot_df['State_Year'],
                            y=pivot_df[metric],
                            name=metric,
                            marker_color='rgb(55, 83, 109)',
                            opacity=0.9,
                            text=[f'{v:.2f}' for v in pivot_df[metric]],
                            textposition='auto'
                        ))

                fig.update_layout(
                    title={'text': f'Metrics Comparison', 'x': 0.5, 'xanchor': 'center'},
                    xaxis_title='States and Years',
                    yaxis_title='Values',
                    barmode='group',
                    xaxis_tickangle=45,
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    margin=dict(l=50, r=50, t=80, b=100),
                    yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
                )
                max_value = max(pivot_df.get(requested_metrics[0], [0]).max(), 0.1)
                fig.update_yaxes(range=[0, max_value * 1.2])
                figures.append(fig)
            else:
                print("No valid data for bar chart after filtering")

    for state in data_by_state_year:
        years = year_dict.get(state, ["2024"])
        if not isinstance(years, list):
            years = [years]
        years = sorted(set(str(y) for y in years if 2015 <= int(y) <= 2024))

        if len(requested_metrics) > 1:
            for year in years:
                if year in data_by_state_year[state]:
                    values = data_by_state_year[state][year]
                    if any(v > 0 for v in values):
                        title = f'Metrics for {state} ({year})'
                        fig = go.Figure(data=[
                            go.Bar(
                                x=requested_metrics,
                                y=values,
                                text=[f'{v:.2f}' for v in values],
                                textposition='auto',
                                marker_color=px.colors.qualitative.Plotly,
                                opacity=0.9
                            )
                        ])
                        fig.update_layout(
                            title={'text': title, 'x': 0.5, 'xanchor': 'center'},
                            xaxis_title='Metrics',
                            yaxis_title='Proportion',
                            xaxis_tickangle=45,
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(size=12),
                            margin=dict(l=50, r=50, t=80, b=100),
                            yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
                        )
                        max_value = max(values + [0.1])
                        fig.update_yaxes(range=[0, max_value * 1.5])
                        figures.append(fig)

            if len(years) > 1:
                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                for i, year in enumerate(years):
                    if year in data_by_state_year[state]:
                        values = data_by_state_year[state][year]
                        fig.add_trace(go.Bar(
                            x=requested_metrics,
                            y=values,
                            name=f"{year}",
                            text=[f'{v:.2f}' for v in values],
                            textposition='auto',
                            marker_color=colors[i % len(colors)],
                            opacity=0.9
                        ))

                fig.update_layout(
                    title={'text': f'Metrics Comparison for {state} ({min(years)}–{max(years)})', 'x': 0.5, 'xanchor': 'center'},
                    xaxis_title='Metrics',
                    yaxis_title='Proportion',
                    barmode='group',
                    xaxis_tickangle=45,
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    margin=dict(l=50, r=50, t=80, b=100),
                    yaxis=dict(gridcolor='rgba(200,200,200,0.3)')
                )
                max_value = max(max(data_by_state_year[state][y]) for y in years if y in data_by_state_year[state]) + 0.1
                fig.update_yaxes(range=[0, max_value * 1.2])
                figures.append(fig)

    if "land cover" in query.lower():
        generated_charts = set()
        for state in states:
            years = year_dict.get(state, ["2024"])
            if not isinstance(years, list):
                years = [years]
            years = sorted(set(str(y) for y in years if 2015 <= int(y) <= 2024))
            
            if state not in data_by_state_year:
                print(f"No land cover data for {state}")
                continue
                
            for year in years:
                chart_key = f"{state}_{year}"
                if chart_key in generated_charts:
                    print(f"Skipping duplicate pie chart for {state} {year}")
                    continue
                    
                if year in data_by_state_year[state]:
                    values = data_by_state_year[state][year]
                    if not any(v > 0 for v in values):
                        print(f"No non-zero land cover values for {state} {year}")
                        continue
                        
                    non_zero_metrics = [m for m, v in zip(requested_metrics, values) if v > 0]
                    non_zero_values = [v for v in values if v > 0]
                    
                    if non_zero_metrics:
                        fig = go.Figure(data=[
                            go.Pie(
                                labels=non_zero_metrics,
                                values=non_zero_values,
                                textinfo='label+percent',
                                insidetextorientation='radial',
                                marker=dict(colors=px.colors.qualitative.Plotly),
                                hole=0.3
                            )
                        ])
                        fig.update_layout(
                            title={'text': f'Land Cover Distribution for {state} ({year})', 'x': 0.5, 'xanchor': 'center'},
                            showlegend=True,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(size=12),
                            margin=dict(l=50, r=50, t=80, b=50)
                        )
                        figures.append(fig)
                        generated_charts.add(chart_key)
                        print(f"Generated Pie Chart for {state} {year}: {non_zero_metrics}")
                    else:
                        print(f"No non-zero land cover metrics for {state} {year}")

    if len(states) == 1:
        state = states[0]
        years = year_dict.get(state, ["2024"])
        if isinstance(years, list) and len(years) > 1:
            years = [str(y) for y in years if 2015 <= int(y) <= 2024]
            if years and state in data_by_state_year:
                fig = go.Figure()
                plotted = False
                colors = px.colors.qualitative.Plotly
                for i, metric in enumerate(requested_metrics):
                    values = [data_by_state_year[state].get(y, [0.0] * len(requested_metrics))[requested_metrics.index(metric)]
                              for y in years]
                    if any(v > 0 for v in values):
                        fig.add_trace(go.Scatter(
                            x=[int(y) for y in years],
                            y=values,
                            mode='lines+markers',
                            name=metric,
                            line=dict(color=colors[i % len(colors)], width=2),
                            marker=dict(size=8),
                            text=[f'{v:.2f}' for v in values],
                            hovertemplate='%{x}: %{y:.2f}<extra></extra>'
                        ))
                        plotted = True
                if plotted:
                    fig.update_layout(
                        title={'text': f'Trends for {state} ({min(years)}–{max(years)})', 'x': 0.5, 'xanchor': 'center'},
                        xaxis_title='Year',
                        yaxis_title='Proportion',
                        showlegend=True,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        margin=dict(l=50, r=50, t=80, b=50),
                        xaxis=dict(tickvals=[int(y) for y in years]),
                        yaxis=dict(gridcolor='rgba(200,200,200,0.3)', range=[0, 1.0])
                    )
                    figures.append(fig)
                else:
                    print(f"No data for {state} across years {years}")

    if len(states) > 1:
        years = set()
        for state in states:
            years.update([str(y) for y in year_dict.get(state, ["2024"]) if 2015 <= int(y) <= 2024])
        if years:
            for metric in requested_metrics:
                fig = go.Figure()
                plotted = False
                colors = px.colors.qualitative.Plotly
                for i, state in enumerate(states):
                    state_years = [str(y) for y in year_dict.get(state, ["2024"]) if y in years]
                    values = [data_by_state_year.get(state, {}).get(y, [0.0] * len(requested_metrics))[requested_metrics.index(metric)]
                              for y in state_years]
                    if any(v > 0 for v in values):
                        fig.add_trace(go.Scatter(
                            x=[int(y) for y in state_years],
                            y=values,
                            mode='lines+markers',
                            name=f"{state} ({metric})",
                            line=dict(color=colors[i % len(colors)], width=2),
                            marker=dict(size=8),
                            text=[f'{v:.2f}' for v in values],
                            hovertemplate='%{x}: %{y:.2f}<extra></extra>'
                        ))
                        plotted = True
                if plotted:
                    year_range = f"{min(years)}–{max(years)}" if len(years) > 1 else years.pop()
                    fig.update_layout(
                        title={'text': f'{metric} Comparison for {", ".join(states)} ({year_range})', 'x': 0.5, 'xanchor': 'center'},
                        xaxis_title='Year',
                        yaxis_title='Proportion',
                        showlegend=True,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        margin=dict(l=50, r=50, t=80, b=50),
                        xaxis=dict(tickvals=[int(y) for y in years]),
                        yaxis=dict(gridcolor='rgba(200,200,200,0.3)', range=[0, 1.0])
                    )
                    figures.append(fig)
                else:
                    print(f"No data for {metric} across states {states}")

    print(f"Generated Figures: {len(figures)}")
    return figures
