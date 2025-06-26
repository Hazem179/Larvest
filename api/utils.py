import mercantile
from PIL import Image
from io import BytesIO
from vcube.tile import TileProcessor
import os
import folium
import tempfile
import datetime


async def generate_tiles_and_map(
    min_lon=30.304434642130218, 
    min_lat=30.174682637534644, 
    max_lon=30.42143846734797, 
    max_lat=30.283438554006977,
    zoom_level=12,
    start_date="2025-01-01",
    end_date="2025-03-01",
    cloud_cover=30,
    band1="red",
    band2="nir",
    formula="(band2-band1)/(band2+band1)",
    colormap_str="RdYlGn"
):
    media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
    os.makedirs(media_dir, exist_ok=True)
    tiles_dir = os.path.join(media_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, zooms=zoom_level))
    print(f"Number of tiles to process: {len(tiles)}")
    tile_processor = TileProcessor()
    results = []
    for tile in tiles:
        x, y, z = tile.x, tile.y, tile.z
        print(f"Processing tile: {x}_{y}_{z}")
        try:
            image_bytes, feature = await tile_processor.cached_generate_tile(
                x=x,
                y=y,
                z=z,
                start_date=start_date,
                end_date=end_date,
                cloud_cover=cloud_cover,
                band1=band1,
                band2=band2,
                formula=formula,
                colormap_str=colormap_str,
            )
            print(f"Image bytes size: {len(image_bytes)} bytes")
            if not image_bytes or len(image_bytes) == 0:
                print(f"Warning: Empty image bytes for tile {x}_{y}_{z}")
                continue
            image = Image.open(BytesIO(image_bytes))
            print(f"Tile: {x}_{y}_{z}")
            print(f"Date: {feature['properties']['datetime']}")
            print(f"Cloud Cover: {feature['properties']['eo:cloud_cover']}%")
            
            # Save the image to the media/tiles directory
            filename = f'tile_{x}_{y}_{z}.png'
            file_path = os.path.join(tiles_dir, filename)
            image.save(file_path)
            
            # Create relative path from media directory
            relative_path = os.path.join("media/tiles", filename)
            
            print(f"Saved image to: {file_path}")
            results.append({
                'tile': f"{x}_{y}_{z}",
                'date': feature['properties']['datetime'],
                'cloud_cover': feature['properties']['eo:cloud_cover'],
                'file_path': relative_path,
                'x': x,
                'y': y,
                'z': z
            })
        except Exception as e:
            print(f"Error processing tile {x}_{y}_{z}: {str(e)}")
            continue
    map_path = None
    map_html = None
    if results:
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level-1, tiles="OpenStreetMap")
        for result in results:
            x, y, z = result['x'], result['y'], result['z']
            tile = mercantile.Tile(x=x, y=y, z=z)
            bounds = mercantile.bounds(tile)
            folium_bounds = [[bounds.south, bounds.west], [bounds.north, bounds.east]]
            # Use full path for folium but relative path in results
            image_path = os.path.join(media_dir, result['file_path'])
            if os.path.exists(image_path):
                folium.raster_layers.ImageOverlay(
                    image=image_path,
                    bounds=folium_bounds,
                    opacity=0.8, 
                    interactive=True,
                    name=f"Tile {x}_{y}_{z}",
                    overlay=True,
                    control=True,
                    popup=f"Date: {result['date']}<br>Cloud Cover: {result['cloud_cover']}%"
                ).add_to(m)
                print(f"Added tile {x}_{y}_{z} to map")
            else:
                print(f"Image not found: {image_path}")
        folium.LayerControl().add_to(m)
        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
        
        # Create a directory for maps if it doesn't exist
        maps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        
        # Save map to a specific location with a more descriptive filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        map_filename = f"satellite_map_{int(center_lat)}_{int(center_lon)}_{timestamp}.html"
        map_file = os.path.join(maps_dir, map_filename)
        m.save(map_file)
        map_path = map_file
        
        # Read the HTML content from the saved file
        with open(map_file, 'r', encoding='utf-8') as f:
            map_html = f.read()
            
    # Return results, map_path, and the HTML content
    return results, map_path, map_html
