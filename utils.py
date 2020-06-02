# Collection of utility functions

def add_seasons(df_in, copy=True):
  if copy:
    df = df_in.copy()
  else:
    df = df_in
    
  m = df['messdatum_date'].dt.month
  df.loc[(m == 3) | (m == 4) | (m == 5), 'season'] = 1
  df.loc[(m == 6) | (m == 7) | (m == 8), 'season'] = 2
  df.loc[(m == 9) | (m == 10) | (m == 11), 'season'] = 3
  df.loc[(m == 12) | (m == 1) | (m == 0), 'season'] = 4

  # Make quarters: Spring 2010 is 2010.0; Summer 2010.25 ...
  df['quarter'] = df['messdatum_date'].dt.year + df['season'] / 4 - 0.25
  # Correction for January to be counted to the winter of the previous year.
  df.loc[m == 1, 'quarter'] -= 1

  return df