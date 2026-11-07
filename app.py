import numpy as np
import pandas as pd
import plotly.graph_objects as go


def calculate_volume_profile(df: pd.DataFrame, bins: int = 50):
  """Calculates Point of Control (POC), Value Area High (VAH),

  and Value Area Low (VAL) from a given DataFrame of candles.
  """
  if df.empty or "High" not in df.columns or "Low" not in df.columns:
    return None

  price_min = df["Low"].min()
  price_max = df["High"].max()
  if price_min == price_max:
    return None

  price_bins = np.linspace(price_min, price_max, bins)
  volume_at_price = np.zeros(bins - 1)

  for _, row in df.iterrows():
    c_low, c_high, c_vol = row["Low"], row["High"], row["Volume"]
    if c_high == c_low or c_vol == 0:
      continue

    bin_indices = np.where(
        (price_bins[:-1] <= c_high) & (price_bins[1:] >= c_low)
    )[0]
    if len(bin_indices) > 0:
      vol_per_bin = c_vol / len(bin_indices)
      for idx in bin_indices:
        volume_at_price[idx] += vol_per_bin

  bin_centers = (price_bins[:-1] + price_bins[1:]) / 2
  poc_idx = np.argmax(volume_at_price)
  poc_price = bin_centers[poc_idx]

  # Calculate 70% Value Area
  total_vol = np.sum(volume_at_price)
  if total_vol == 0:
    return None
  target_vol = total_vol * 0.70

  sorted_indices = np.argsort(volume_at_price)[::-1]
  accumulated_vol = 0
  va_indices = []

  for idx in sorted_indices:
    accumulated_vol += volume_at_price[idx]
    va_indices.append(idx)
    if accumulated_vol >= target_vol:
      break

  val_price = bin_centers[min(va_indices)]
  vah_price = bin_centers[max(va_indices)]

  return {
      "poc": poc_price,
      "val": min(val_price, vah_price),
      "vah": max(val_price, vah_price),
  }


def get_prior_week_profile(df: pd.DataFrame):
  """Splits data by week, isolating the prior completed week's volume profile."""
  if "Time" not in df.columns:
    # Ensure datetime index is converted
    df = df.copy()
    df["Time"] = pd.to_datetime(df.index)

  df["YearWeek"] = df["Time"].dt.strftime("%Y-%U")
  unique_weeks = df["YearWeek"].unique()

  if len(unique_weeks) < 2:
    return None  # Need at least current week + 1 prior week

  prior_week_id = unique_weeks[-2]
  prior_df = df[df["YearWeek"] == prior_week_id]

  return calculate_volume_profile(prior_df)


def evaluate_weekly_strategy(current_df: pd.DataFrame, profile: dict):
  """Evaluates price action rules:

  - Breakout above VAH + pullback to VAH -> Limit Buy (Stop at VAL)
  - Breakdown below VAL + pullback to VAL -> Limit Sell (Stop at VAH)
  """
  if not profile:
    return {"signal": None}

  vah = profile["vah"]
  val = profile["val"]

  latest_close = current_df["Close"].iloc[-1]
  recent_high = current_df["High"].max()
  recent_low = current_df["Low"].min()

  signal = None
  entry_price = None
  stop_loss = None

  # Bullish Rule: Broke prior week VAH to make new high, pulling back to retest VAH
  if recent_high > vah and abs(latest_close - vah) / vah <= 0.0015:
    signal = "BULLISH_LIMIT_BUY"
    entry_price = vah
    stop_loss = val

  # Bearish Rule: Broke prior week VAL to make new low, pulling back to retest VAL
  elif recent_low < val and abs(latest_close - val) / val <= 0.0015:
    signal = "BEARISH_LIMIT_SELL"
    entry_price = val
    stop_loss = vah

  return {
      "signal": signal,
      "entry": entry_price,
      "stop_loss": stop_loss,
      "vah": vah,
      "val": val,
  }


def plot_chart_with_weekly_profile(df: pd.DataFrame, profile: dict):
  """Renders Plotly candlestick chart with horizontal weekly VAH/VAL lines printing

  across the new week.
  """
  fig = go.Figure()

  # Add Candlesticks
  fig.add_trace(
      go.Candlestick(
          x=df.index,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name="Price Action",
      )
  )

  if profile:
    vah = profile["vah"]
    val = profile["val"]
    poc = profile["poc"]
    start_time = df.index[0]
    end_time = df.index[-1]

    # Plot Prior Week's VAH (Blue/Cyan)
    fig.add_trace(
        go.Scatter(
            x=[start_time, end_time],
            y=[vah, vah],
            mode="lines",
            name=f"Prior Week VAH: {vah:.5f}",
            line=dict(color="cyan", dash="dash", width=2),
        )
    )

    # Plot Prior Week's VAL (Orange/Gold)
    fig.add_trace(
        go.Scatter(
            x=[start_time, end_time],
            y=[val, val],
            mode="lines",
            name=f"Prior Week VAL: {val:.5f}",
            line=dict(color="orange", dash="dash", width=2),
        )
    )

    # Plot Prior Week's POC (Green)
    fig.add_trace(
        go.Scatter(
            x=[start_time, end_time],
            y=[poc, poc],
            mode="lines",
            name=f"Prior Week POC: {poc:.5f}",
            line=dict(color="green", dash="dot", width=1.5),
        )
    )

  fig.update_layout(
      title="APEX AI Trading Desk - Weekly Volume Profile Strategy",
      xaxis_title="Time",
      yaxis_title="Price",
      template="plotly_dark",
      xaxis_rangeslider_visible=False,
  )

  return fig
