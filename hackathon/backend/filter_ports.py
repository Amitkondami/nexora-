import json

input_file = '/Users/amit_0703/hackathon/frontend/ports.json'
output_file = '/Users/amit_0703/hackathon/frontend/optimized_ports.json'

target_countries = ["Australia", "United States", "Mozambique", "Indonesia"]

# Comprehensive list of East Coast Indian Ports found in the dataset
east_coast_india = [
    'PARADIP', 
    'VISHAKHAPATNAM', 
    'HALDIA PORT', 
    'GOPALPUR', 
    'CALCUTTA',
    'CHENNAI (MADRAS)', 
    'KAMARAJAR PORT', 
    'KAKINADA BAY', 
    'KARAIKAL PORT', 
    'NAGAPPATTINAM', 
    'TUTICORIN', 
    'CUDDALORE', 
    'MACHILIPATNAM', 
    'PONDICHERRY'
]

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

original_count = len(data.get('ports', []))
filtered_ports = []

for p in data.get('ports', []):
    country = p.get('country')
    port_name = p.get('wpi_port_name')
    
    # If it's one of the other countries, keep it
    if country in target_countries:
        filtered_ports.append(p)
    # If it's India, ONLY keep it if it's on the East Coast list
    elif country == "India":
        if port_name in east_coast_india:
            filtered_ports.append(p)

data['ports'] = filtered_ports
data['metadata']['record_count'] = len(filtered_ports)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f"Optimization complete! Reduced from {original_count} to {len(filtered_ports)} highly relevant ports (India restricted to East Coast only).")
