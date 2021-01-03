""" 50 states mapped from abbreviation to state name """
state_d = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 
    'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 
    'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 
    'WI': 'Wisconsin', 'WY': 'Wyoming'}

""" flip the keys and values so rstate_d['Texas'] = 'TX', e.g. """
rstate_d = dict([(v,k) for (k,v) in state_d.items()])

""" 5 territories (in JHU data) mapped from abbreviation to territory name """
territory_d = {'VI': 'Virgin Islands', 'MP': 'Northern Mariana Islands', 'GU': 'Guam',
                'PR': 'Puerto Rico', 'AS': 'American Samoa'}

""" flip the keys and values so rstate_d['Guam'] = 'GU', e.g. """
rterritory_d = dict([(v,k) for (k,v) in territory_d.items()])

merged_d = dict(list(state_d.items()) + list(territory_d.items()))
rmerged_d = dict(list(rstate_d.items()) + list(rterritory_d.items()))
