import csv
import random

# Sample descriptive words for generating captions
landscapes = ['urban', 'rural', 'coastal', 'industrial', 'residential']
features = ['buildings', 'roads', 'vegetation', 'water bodies', 'infrastructure']
details = ['dense', 'sparse', 'organized', 'scattered', 'developed']
colors = ['green', 'grey', 'blue', 'brown', 'mixed']

def generate_caption():
    """Generate a random but plausible caption for a satellite image"""
    return f"A {random.choice(landscapes)} area with {random.choice(details)} {random.choice(features)} and {random.choice(colors)} tones"

# Generate sample data
sample_data = []
for i in range(100):  # Generate 100 sample entries
    image_path = f"images/satellite_{i:03d}.jpg"
    caption = generate_caption()
    sample_data.append([image_path, caption])

# Write to CSV
with open('captions.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['image_path', 'caption'])  # Header
    writer.writerows(sample_data)

print("Generated captions.csv with 100 sample entries")
print("\nFirst few entries:")
for i in range(3):
    print(f"Path: {sample_data[i][0]}")
    print(f"Caption: {sample_data[i][1]}\n")
