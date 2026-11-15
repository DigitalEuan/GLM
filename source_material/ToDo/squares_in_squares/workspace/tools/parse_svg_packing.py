#!/usr/bin/env python3
"""
Parse David Ellsworth's special SVG square packing format.
Extracts individual unit squares with their positions and rotations.
"""

# With use_parser_g enabled, a <parser:g> tag indicates to process only the
# children of that tag and skip its siblings. For an SVG to use this it must
# have xmlns:parser="urn:parser" in its <svg> tag.
use_parser_g = True

import xml.etree.ElementTree as ET
import re
import math
from decimal import Decimal, getcontext

import mpmath

# High-precision trigonmetric functions
def hp_sin(angle_decimal, precision):
    mpmath.mp.dps = precision + 10
    result = mpmath.sin(mpmath.mpf(str(angle_decimal)))
    return Decimal(mpmath.nstr(result, precision + 20))
def hp_cos(angle_decimal, precision):
    mpmath.mp.dps = precision + 10
    result = mpmath.cos(mpmath.mpf(str(angle_decimal)))
    return Decimal(mpmath.nstr(result, precision + 20))
def hp_atan2(y_decimal, x_decimal, precision):
    mpmath.mp.dps = precision + 10
    result = mpmath.atan2(mpmath.mpf(str(y_decimal)), mpmath.mpf(str(x_decimal)))
    return Decimal(mpmath.nstr(result, precision + 20))
def hp_pi(precision):
    mpmath.mp.dps = precision + 10
    return Decimal(mpmath.nstr(mpmath.pi, precision + 20))

class Transform:
    """2D affine transformation matrix"""
    def __init__(self):
        self.a = Decimal(1)
        self.b = Decimal(0)
        self.c = Decimal(0)
        self.d = Decimal(1)
        self.e = Decimal(0)
        self.f = Decimal(0)
    
    def copy(self):
        t = Transform()
        t.a, t.b, t.c, t.d, t.e, t.f = self.a, self.b, self.c, self.d, self.e, self.f
        return t
    
    def multiply(self, other):
        result = Transform()
        result.a = self.a * other.a + self.c * other.b
        result.b = self.b * other.a + self.d * other.b
        result.c = self.a * other.c + self.c * other.d
        result.d = self.b * other.c + self.d * other.d
        result.e = self.a * other.e + self.c * other.f + self.e
        result.f = self.b * other.e + self.d * other.f + self.f
        return result
    
    def apply_point(self, x, y):
        new_x = self.a * x + self.c * y + self.e
        new_y = self.b * x + self.d * y + self.f
        return new_x, new_y
    
    def get_rotation(self, precision=50, square_id=None):
        threshold = Decimal(10) ** (-(precision - 10)) if precision > 10 else Decimal("1e-6")
        
        if abs(self.b) < threshold and abs(self.c) < threshold:
            return Decimal(0)
        
        if abs(self.a) < threshold and abs(self.d) < threshold:
            if self.b > 0:
                return hp_pi(precision) / Decimal(2)
            else:
                return -hp_pi(precision) / Decimal(2)
        
        if abs(self.b) < threshold and abs(self.c) < threshold:
            if self.a < 0:
                return hp_pi(precision)
        
        angle_rad = hp_atan2(self.b, self.a, precision)
        
        if abs(angle_rad) < threshold:
            return Decimal(0)
        
        return angle_rad


def parse_entities(svg_content):
    """Parse ENTITY definitions from DTD"""
    entities = {}
    pattern = r'<!ENTITY\s+(\w+)\s+"([^"]+)"\s*>'
    for match in re.finditer(pattern, svg_content):
        entities[match.group(1)] = match.group(2)
    return entities


def replace_entities(text, entities):
    """Replace &entity; references with values"""
    if not text:
        return text
    for name, value in entities.items():
        text = text.replace(f'&{name};', value)
    return text


def parse_transform_attr(transform_str, entities, precision=50):
    """Parse SVG transform attribute and return Transform object"""
    if not transform_str:
        return Transform()
    
    transform_str = replace_entities(transform_str, entities)
    result = Transform()
    
    pattern = r'(\w+)\s*\(([^)]+)\)'
    for match in re.finditer(pattern, transform_str):
        func_name = match.group(1)
        args = match.group(2).strip()
        
        t = Transform()
        
        if func_name == 'translate':
            parts = args.split()
            tx = Decimal(parts[0]) if parts else Decimal(0)
            ty = Decimal(parts[1]) if len(parts) > 1 else Decimal(0)
            t.e = tx
            t.f = ty
            
        elif func_name == 'rotate':
            old_prec = getcontext().prec
            getcontext().prec = precision + 20
            
            angle_deg = Decimal(args)
            angle_rad = angle_deg * hp_pi(precision) / Decimal(180)
            
            getcontext().prec = old_prec
            
            t.a = hp_cos(angle_rad, precision)
            t.b = hp_sin(angle_rad, precision)
            t.c = -hp_sin(angle_rad, precision)
            t.d = hp_cos(angle_rad, precision)
            
        elif func_name == 'scale':
            parts = args.split()
            sx = Decimal(parts[0]) if parts else Decimal(1)
            sy = Decimal(parts[1]) if len(parts) > 1 else sx
            t.a = sx
            t.d = sy
        
        result = result.multiply(t)
    
    return result


def parse_path_to_vertices(path_d):
    """
    Parse SVG path data into a list of vertices.
    Returns list of (x, y) Decimal tuples forming the polygon.
    """
    path_d = path_d.strip()
    
    # Tokenize the path - split by commands but handle negative numbers
    tokens = re.split(r'([MmLlHhVvZz])', path_d)
    tokens = [t.strip() for t in tokens if t.strip()]
    
    vertices = []
    current_x = Decimal(0)
    current_y = Decimal(0)
    start_x = Decimal(0)
    start_y = Decimal(0)
    
    i = 0
    while i < len(tokens):
        if tokens[i] in 'MLHVZmlhvz':
            cmd = tokens[i]
            i += 1
            
            if cmd == 'M':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x = Decimal(coords[0])
                        current_y = Decimal(coords[1])
                        start_x = current_x
                        start_y = current_y
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'm':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x += Decimal(coords[0])
                        current_y += Decimal(coords[1])
                        start_x = current_x
                        start_y = current_y
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'V':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_y = Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'v':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_y += Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'H':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_x = Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'h':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_x += Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'L':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x = Decimal(coords[0])
                        current_y = Decimal(coords[1])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'l':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x += Decimal(coords[0])
                        current_y += Decimal(coords[1])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'Z' or cmd == 'z':
                # Close path - only add closing vertex if different from start
                if vertices and (current_x != start_x or current_y != start_y):
                    vertices.append((start_x, start_y))
                current_x = start_x
                current_y = start_y
        else:
            i += 1
    
    return vertices


def remove_collinear_vertices(vertices, tolerance=None):
    """
    Remove vertices that are collinear with their neighbors.
    For orthogonal polygons, this removes points on straight edges.
    Also removes duplicate close points first.
    """
    if len(vertices) < 3:
        return vertices
    
    if tolerance is None:
        tolerance = Decimal(10) ** -(precision - 2)
    
    # First, remove duplicate consecutive vertices (like close points)
    cleaned = []
    for i, v in enumerate(vertices):
        if not cleaned:
            cleaned.append(v)
        else:
            prev = cleaned[-1]
            if abs(v[0] - prev[0]) > tolerance or abs(v[1] - prev[1]) > tolerance:
                cleaned.append(v)
    
    # Also check if last equals first
    if len(cleaned) > 1:
        if abs(cleaned[-1][0] - cleaned[0][0]) <= tolerance and abs(cleaned[-1][1] - cleaned[0][1]) <= tolerance:
            cleaned = cleaned[:-1]
    
    if len(cleaned) < 3:
        return cleaned
    
    result = []
    n = len(cleaned)
    
    for i in range(n):
        prev_idx = (i - 1) % n
        next_idx = (i + 1) % n
        
        p1 = cleaned[prev_idx]
        p2 = cleaned[i]
        p3 = cleaned[next_idx]
        
        # Check if p2 is on the line segment from p1 to p3
        # For orthogonal paths, a point is collinear if either:
        # - x values are all the same (vertical edge)
        # - y values are all the same (horizontal edge)
        
        x_same = abs(p1[0] - p2[0]) <= tolerance and abs(p2[0] - p3[0]) <= tolerance
        y_same = abs(p1[1] - p2[1]) <= tolerance and abs(p2[1] - p3[1]) <= tolerance
        
        if not (x_same or y_same):
            # This is a corner, keep it
            result.append(p2)
    
    return result


def polygon_area_signed(vertices):
    """
    Calculate signed area of polygon using the shoelace formula.
    Positive = counter-clockwise, Negative = clockwise
    """
    if len(vertices) < 3:
        return Decimal(0)
    
    area = Decimal(0)
    n = len(vertices)
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    return area / Decimal(2)


def square_fully_inside(center_x, center_y, vertices, tolerance):
    """Check if ALL 4 corners of a unit square are inside the polygon."""
    half = Decimal('0.5')
    corners = [
        (center_x - half + tolerance, center_y - half + tolerance),
        (center_x + half - tolerance, center_y - half + tolerance),
        (center_x + half - tolerance, center_y + half - tolerance),
        (center_x - half + tolerance, center_y + half - tolerance),
    ]
    for cx, cy in corners:
        if not point_in_polygon(cx, cy, vertices):
            return False
    return True


def fill_orthogonal_polygon_with_squares(vertices, tolerance=None, fill_rule='nonzero'):
    """
    Fill an orthogonal polygon with unit squares using region subtraction.
    
    Algorithm:
    1. Convert polygon to a region data structure (y-bands with x-intervals)
    2. Iteratively find a unit square at a corner of the region
    3. Subtract that square from the region
    4. Repeat until region is empty
    
    fill_rule: 'nonzero' (default) or 'evenodd' - determines how overlapping/nested paths are filled
    """
    if len(vertices) < 4:
        return []
    
    if tolerance is None:
        tolerance = Decimal('1e-30')
    
    # Remove collinear vertices to get just corners
    corners = remove_collinear_vertices(vertices, tolerance)
    if len(corners) < 4:
        return []
    
    # Convert polygon to region with fill-rule handling
    region = polygon_to_region(corners, tolerance, fill_rule)
    
    square_centers = []
    
    # Iteratively extract squares from corners
    max_iterations = 10000  # Safety limit
    for _ in range(max_iterations):
        if region_is_empty(region, tolerance):
            break
        
        # Find a unit square at a corner of the region
        square = find_corner_square(region, tolerance)
        if square is None:
            # No more corner squares found, but region not empty - this shouldn't happen
            # for valid orthogonal packings
            break
        
        # Verify the square is fully contained in the region
        if not square_in_region(square, region, tolerance):
            break
        
        # Subtract the square from the region
        region = subtract_square_from_region(region, square, tolerance)
        
        # Record the square center
        x, y = square
        center_x = x + Decimal('0.5')
        center_y = y + Decimal('0.5')
        square_centers.append((center_x, center_y))
    
    return square_centers


def polygon_to_region(corners, tolerance, fill_rule='nonzero'):
    """
    Convert an orthogonal polygon (list of corner vertices) to a region.
    Region is represented as a list of (y_start, y_end, x_intervals) tuples,
    where x_intervals is a list of (x_start, x_end) tuples.
    
    For fill_rule='nonzero': Uses winding number to determine inside/outside.
                             Clockwise paths add, counter-clockwise subtract.
    For fill_rule='evenodd': Uses crossing count parity.
    """
    # Get all unique y-coordinates (these define the y-bands)
    y_coords = sorted(set(v[1] for v in corners))
    
    region = []
    
    for i in range(len(y_coords) - 1):
        y_start = y_coords[i]
        y_end = y_coords[i + 1]
        
        # Find x-intervals at this y-band by scanning horizontal line through middle
        test_y = (y_start + y_end) / 2
        
        # Find all x-coordinates where edges cross this y-level, with direction info
        crossings = []  # List of (x, direction) where direction is +1 (upward) or -1 (downward)
        n = len(corners)
        for j in range(n):
            p1 = corners[j]
            p2 = corners[(j + 1) % n]
            
            y1, y2 = p1[1], p2[1]
            
            # Check if edge crosses test_y (not just touches)
            if (y1 < test_y < y2) or (y2 < test_y < y1):
                # Determine crossing direction (for nonzero fill rule)
                direction = 1 if y2 > y1 else -1  # +1 if edge goes upward, -1 if downward
                
                # Find x at test_y
                if abs(p2[0] - p1[0]) < tolerance:
                    # Vertical line
                    crossings.append((p1[0], direction))
                else:
                    # Should not happen for orthogonal polygons at non-vertex y
                    t = (test_y - y1) / (y2 - y1)
                    x_cross = p1[0] + t * (p2[0] - p1[0])
                    crossings.append((x_cross, direction))
        
        # Sort crossings by x-coordinate
        crossings.sort(key=lambda c: c[0])
        
        # Build x-intervals based on fill rule
        x_intervals = []
        
        if fill_rule == 'evenodd':
            # Simple pairing: every pair of crossings defines an interval
            for j in range(0, len(crossings) - 1, 2):
                if j + 1 < len(crossings):
                    x_intervals.append((crossings[j][0], crossings[j + 1][0]))
        else:
            # nonzero: track winding number
            winding = 0
            interval_start = None
            
            for x, direction in crossings:
                prev_winding = winding
                winding += direction
                
                # Transition from outside to inside
                if prev_winding == 0 and winding != 0:
                    interval_start = x
                # Transition from inside to outside
                elif prev_winding != 0 and winding == 0:
                    if interval_start is not None:
                        x_intervals.append((interval_start, x))
                    interval_start = None
        
        if x_intervals:
            region.append((y_start, y_end, x_intervals))
    
    return region


def region_is_empty(region, tolerance):
    """Check if region has zero area."""
    for y_start, y_end, x_intervals in region:
        for x_start, x_end in x_intervals:
            if x_end - x_start > tolerance and y_end - y_start > tolerance:
                return False
    return True


def find_corner_square(region, tolerance):
    """
    Find a unit square that sits at a corner of the region.
    Returns (x, y) of the bottom-left corner of the square, or None if not found.
    """
    # Collect all corner points of the region
    corners = []
    for y_start, y_end, x_intervals in region:
        for x_start, x_end in x_intervals:
            corners.append((x_start, y_start))  # bottom-left
            corners.append((x_end, y_start))    # bottom-right
            corners.append((x_start, y_end))    # top-left
            corners.append((x_end, y_end))      # top-right
    
    # Try each corner as potential bottom-left of a unit square
    for cx, cy in corners:
        square = (cx, cy)
        if square_in_region(square, region, tolerance):
            return square
    
    # Also try corners offset by -1 (for top-right corners becoming bottom-left)
    for cx, cy in corners:
        for dx, dy in [(-1, 0), (0, -1), (-1, -1)]:
            square = (cx + Decimal(dx), cy + Decimal(dy))
            if square_in_region(square, region, tolerance):
                return square
    
    return None


def square_in_region(square, region, tolerance):
    """
    Check if a unit square (given by bottom-left corner) is fully contained in the region.
    """
    x, y = square
    sq_left = x
    sq_right = x + Decimal(1)
    sq_bottom = y
    sq_top = y + Decimal(1)
    
    # The square must be fully covered by the region
    # Check each horizontal slice of the square against the region's x-intervals
    
    for y_start, y_end, x_intervals in region:
        # Check overlap between square's y-range and this band's y-range
        overlap_bottom = max(sq_bottom, y_start)
        overlap_top = min(sq_top, y_end)
        
        if overlap_top <= overlap_bottom + tolerance:
            continue  # No y-overlap with this band
        
        # For this y-band, check if the square's x-range is covered
        sq_x_covered = Decimal(0)
        for x_start, x_end in x_intervals:
            overlap_left = max(sq_left, x_start)
            overlap_right = min(sq_right, x_end)
            if overlap_right > overlap_left + tolerance:
                sq_x_covered += overlap_right - overlap_left
        
        # The square's full width must be covered in this band
        if sq_x_covered < Decimal(1) - tolerance:
            return False
    
    # Also verify the square's full y-range is covered
    y_covered = Decimal(0)
    for y_start, y_end, x_intervals in region:
        overlap_bottom = max(sq_bottom, y_start)
        overlap_top = min(sq_top, y_end)
        
        if overlap_top <= overlap_bottom + tolerance:
            continue
        
        # Check if full x-width is covered in this band
        for x_start, x_end in x_intervals:
            if x_start <= sq_left + tolerance and x_end >= sq_right - tolerance:
                y_covered += overlap_top - overlap_bottom
                break
    
    return y_covered >= Decimal(1) - tolerance


def subtract_square_from_region(region, square, tolerance):
    """
    Subtract a unit square from the region.
    Returns the new region.
    """
    x, y = square
    sq_left = x
    sq_right = x + Decimal(1)
    sq_bottom = y
    sq_top = y + Decimal(1)
    
    new_region = []
    
    for y_start, y_end, x_intervals in region:
        # Check if this band overlaps with the square vertically
        if y_end <= sq_bottom + tolerance or y_start >= sq_top - tolerance:
            # No overlap, keep band as-is
            new_region.append((y_start, y_end, x_intervals))
            continue
        
        # This band overlaps with the square - need to split/modify
        
        # Part below the square
        if y_start < sq_bottom - tolerance:
            new_region.append((y_start, sq_bottom, x_intervals[:]))
        
        # Part overlapping with square (subtract x-range)
        overlap_bottom = max(y_start, sq_bottom)
        overlap_top = min(y_end, sq_top)
        
        if overlap_top > overlap_bottom + tolerance:
            new_intervals = []
            for x_start, x_end in x_intervals:
                # Subtract [sq_left, sq_right] from [x_start, x_end]
                if x_end <= sq_left + tolerance or x_start >= sq_right - tolerance:
                    # No overlap
                    new_intervals.append((x_start, x_end))
                else:
                    # Some overlap - split the interval
                    if x_start < sq_left - tolerance:
                        new_intervals.append((x_start, sq_left))
                    if x_end > sq_right + tolerance:
                        new_intervals.append((sq_right, x_end))
            
            if new_intervals:
                new_region.append((overlap_bottom, overlap_top, new_intervals))
        
        # Part above the square
        if y_end > sq_top + tolerance:
            new_region.append((sq_top, y_end, x_intervals[:]))
    
    # Merge adjacent bands with same x-intervals
    new_region = merge_region_bands(new_region, tolerance)
    
    return new_region


def merge_region_bands(region, tolerance):
    """Merge adjacent y-bands that have identical x-intervals."""
    if not region:
        return region
    
    # Sort by y_start
    region = sorted(region, key=lambda b: b[0])
    
    merged = []
    for band in region:
        if not merged:
            merged.append(band)
            continue
        
        prev_y_start, prev_y_end, prev_intervals = merged[-1]
        y_start, y_end, intervals = band
        
        # Check if bands are adjacent and have same intervals
        if abs(y_start - prev_y_end) < tolerance:
            if intervals_equal(prev_intervals, intervals, tolerance):
                # Merge
                merged[-1] = (prev_y_start, y_end, prev_intervals)
                continue
        
        merged.append(band)
    
    return merged


def intervals_equal(intervals1, intervals2, tolerance):
    """Check if two lists of x-intervals are equal."""
    if len(intervals1) != len(intervals2):
        return False
    
    for (a_start, a_end), (b_start, b_end) in zip(sorted(intervals1), sorted(intervals2)):
        if abs(a_start - b_start) > tolerance or abs(a_end - b_end) > tolerance:
            return False
    
    return True


def point_in_polygon(x, y, vertices):
    """Test if point (x, y) is inside the polygon using ray casting."""
    n = len(vertices)
    inside = False
    
    p1x, p1y = vertices[0]
    for i in range(1, n + 1):
        p2x, p2y = vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def fill_polygon_progressive(vertices, tolerance=None):
    """
    Fill an orthogonal polygon with unit squares using progressive corner filling.
    
    Algorithm:
    1. Start with the full polygon boundary
    2. Find convex corners (90-degree turns into the polygon)
    3. Place a unit square at each convex corner
    4. Subtract those squares from the polygon
    5. Repeat until no more squares can be placed
    
    This handles complex L-shaped and staircase regions correctly.
    """
    if len(vertices) < 4:
        return []
    
    if tolerance is None:
        tolerance = Decimal(10) ** -(precision - 2)
    
    # Remove collinear vertices
    corners = remove_collinear_vertices(vertices)
    if len(corners) < 4:
        return []
    
    # Use the grid-based approach which is more robust for these orthogonal shapes
    return fill_orthogonal_polygon_with_squares(corners, tolerance)


def extract_squares_from_path_v2(path_d, transform, squares, entities, square_id_counter, precision=50, fill_rule='nonzero'):
    """
    Extract squares from filled path using the polygon-filling algorithm.
    Handles multiple subpaths correctly according to fill-rule.
    """
    path_d = path_d.strip()
    
    # Parse ALL subpaths together to handle fill-rule correctly
    # (multiple subpaths can create holes via winding direction)
    all_vertices = parse_path_to_vertices_multi(path_d)
    
    if not all_vertices:
        return
    
    tolerance = Decimal(10) ** -(precision - 2)
    
    # Convert all subpaths to a single region using the fill rule
    region = multi_subpath_to_region(all_vertices, tolerance, fill_rule)
    
    if region_is_empty(region, tolerance):
        return
    
    # Extract squares from the region
    square_centers = []
    max_iterations = 10000
    
    for _ in range(max_iterations):
        if region_is_empty(region, tolerance):
            break
        
        square = find_corner_square(region, tolerance)
        if square is None:
            break
        
        if not square_in_region(square, region, tolerance):
            break
        
        region = subtract_square_from_region(region, square, tolerance)
        
        x, y = square
        center_x = x + Decimal('0.5')
        center_y = y + Decimal('0.5')
        square_centers.append((center_x, center_y))
    
    # Add the found squares
    for center_x, center_y in square_centers:
        tx, ty = transform.apply_point(center_x, center_y)
        theta = transform.get_rotation(precision, square_id_counter[0])
        
        squares.append({
            'id': square_id_counter[0],
            'x': tx,
            'y': ty,
            'theta': theta
        })
        square_id_counter[0] += 1


def parse_path_to_vertices_multi(path_d):
    """
    Parse an SVG path into a list of subpaths, where each subpath is a list of vertices.
    Returns list of vertex lists, one per subpath.
    """
    path_d = path_d.strip()
    
    subpaths = []
    current_subpath = []
    current_x = Decimal(0)
    current_y = Decimal(0)
    start_x = Decimal(0)
    start_y = Decimal(0)
    
    tokens = re.split(r'([MmLlHhVvZz])', path_d)
    tokens = [t.strip() for t in tokens if t.strip()]
    
    i = 0
    while i < len(tokens):
        if tokens[i] in 'MLHVZmlhvz':
            cmd = tokens[i]
            i += 1
            
            if cmd == 'M':
                # Start new subpath
                if current_subpath:
                    subpaths.append(current_subpath)
                current_subpath = []
                
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        try:
                            current_x = Decimal(coords[0])
                            current_y = Decimal(coords[1])
                            start_x, start_y = current_x, current_y
                            current_subpath.append((current_x, current_y))
                        except:
                            pass
                    i += 1
                    
            elif cmd == 'm':
                if current_subpath:
                    subpaths.append(current_subpath)
                current_subpath = []
                
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        try:
                            current_x += Decimal(coords[0])
                            current_y += Decimal(coords[1])
                            start_x, start_y = current_x, current_y
                            current_subpath.append((current_x, current_y))
                        except:
                            pass
                    i += 1
                    
            elif cmd == 'L':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        try:
                            current_x = Decimal(coords[0])
                            current_y = Decimal(coords[1])
                            current_subpath.append((current_x, current_y))
                        except:
                            pass
                    i += 1
                    
            elif cmd == 'l':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        try:
                            current_x += Decimal(coords[0])
                            current_y += Decimal(coords[1])
                            current_subpath.append((current_x, current_y))
                        except:
                            pass
                    i += 1
                    
            elif cmd == 'H':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    try:
                        current_x = Decimal(tokens[i].replace(',', ' ').split()[0])
                        current_subpath.append((current_x, current_y))
                    except:
                        pass
                    i += 1
                    
            elif cmd == 'h':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    try:
                        current_x += Decimal(tokens[i].replace(',', ' ').split()[0])
                        current_subpath.append((current_x, current_y))
                    except:
                        pass
                    i += 1
                    
            elif cmd == 'V':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    try:
                        current_y = Decimal(tokens[i].replace(',', ' ').split()[0])
                        current_subpath.append((current_x, current_y))
                    except:
                        pass
                    i += 1
                    
            elif cmd == 'v':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    try:
                        current_y += Decimal(tokens[i].replace(',', ' ').split()[0])
                        current_subpath.append((current_x, current_y))
                    except:
                        pass
                    i += 1
                    
            elif cmd in 'Zz':
                if current_subpath and (current_x != start_x or current_y != start_y):
                    current_subpath.append((start_x, start_y))
                current_x, current_y = start_x, start_y
        else:
            i += 1
    
    if current_subpath:
        subpaths.append(current_subpath)
    
    return subpaths


def multi_subpath_to_region(subpaths, tolerance, fill_rule='nonzero'):
    """
    Convert multiple subpaths to a region, handling fill-rule correctly.
    Each subpath contributes edges; the fill-rule determines which areas are filled.
    """
    if not subpaths:
        return []
    
    # Collect all corners from all subpaths (for y-coordinate bands)
    all_corners = []
    subpath_corners = []
    
    for vertices in subpaths:
        corners = remove_collinear_vertices(vertices, tolerance)
        if len(corners) >= 3:
            subpath_corners.append(corners)
            all_corners.extend(corners)
    
    if not all_corners:
        return []
    
    # Get all unique y-coordinates
    y_coords = sorted(set(v[1] for v in all_corners))
    
    region = []
    
    for i in range(len(y_coords) - 1):
        y_start = y_coords[i]
        y_end = y_coords[i + 1]
        test_y = (y_start + y_end) / 2
        
        # Collect crossings from ALL subpaths
        crossings = []
        
        for corners in subpath_corners:
            n = len(corners)
            for j in range(n):
                p1 = corners[j]
                p2 = corners[(j + 1) % n]
                
                y1, y2 = p1[1], p2[1]
                
                if (y1 < test_y < y2) or (y2 < test_y < y1):
                    direction = 1 if y2 > y1 else -1
                    
                    if abs(p2[0] - p1[0]) < tolerance:
                        crossings.append((p1[0], direction))
                    else:
                        t = (test_y - y1) / (y2 - y1)
                        x_cross = p1[0] + t * (p2[0] - p1[0])
                        crossings.append((x_cross, direction))
        
        crossings.sort(key=lambda c: c[0])
        
        x_intervals = []
        
        if fill_rule == 'evenodd':
            for j in range(0, len(crossings) - 1, 2):
                if j + 1 < len(crossings):
                    x_intervals.append((crossings[j][0], crossings[j + 1][0]))
        else:
            # nonzero
            winding = 0
            interval_start = None
            
            for x, direction in crossings:
                prev_winding = winding
                winding += direction
                
                if prev_winding == 0 and winding != 0:
                    interval_start = x
                elif prev_winding != 0 and winding == 0:
                    if interval_start is not None:
                        x_intervals.append((interval_start, x))
                    interval_start = None
        
        if x_intervals:
            region.append((y_start, y_end, x_intervals))
    
    return region


def extract_single_region_v2(path_d, transform, squares, entities, square_id_counter, precision=50):
    """
    Extract squares from a single-region filled path using polygon filling.
    """
    # Parse path to vertices
    vertices = parse_path_to_vertices(path_d)
    
    if len(vertices) < 4:
        return
    
    # Try the grid-based filling first
    tolerance = Decimal(10) ** -(precision - 2)
    square_centers = fill_orthogonal_polygon_with_squares(vertices, tolerance)
    
    if square_centers:
        # Add the found squares
        for center_x, center_y in square_centers:
            tx, ty = transform.apply_point(center_x, center_y)
            theta = transform.get_rotation(precision, square_id_counter[0])
            
            squares.append({
                'id': square_id_counter[0],
                'x': tx,
                'y': ty,
                'theta': theta
            })
            square_id_counter[0] += 1
    else:
        # Fall back to the original point-in-polygon scan approach
        extract_single_region_from_path_fallback(path_d, transform, squares, entities, square_id_counter, precision)


def extract_single_region_from_path_fallback(path_d, transform, squares, entities, square_id_counter, precision=50):
    """
    Original fallback method for paths that don't work with grid-based filling.
    """
    path_d = path_d.strip()
    
    # Extract commands and coordinates
    tokens = re.split(r'([MmLlHhVvZz])', path_d)
    tokens = [t.strip() for t in tokens if t.strip()]
    
    vertices = []
    current_x = Decimal(0)
    current_y = Decimal(0)
    start_x = Decimal(0)
    start_y = Decimal(0)
    
    i = 0
    while i < len(tokens):
        if tokens[i] in 'MLHVZmlhvz':
            cmd = tokens[i]
            i += 1
            
            if cmd == 'M':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        try:
                            current_x = Decimal(coords[0])
                            current_y = Decimal(coords[1])
                        except:
                            raise ValueError(f"Invalid coordinate: M {coords}")
                        start_x = current_x
                        start_y = current_y
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'm':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x += Decimal(coords[0])
                        current_y += Decimal(coords[1])
                        start_x = current_x
                        start_y = current_y
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'V':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_y = Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'v':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_y += Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'H':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_x = Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'h':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if coords:
                        current_x += Decimal(coords[0])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'L':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x = Decimal(coords[0])
                        current_y = Decimal(coords[1])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'l':
                if i < len(tokens) and tokens[i] not in 'MLHVZmlhvz':
                    coords = tokens[i].replace(',', ' ').split()
                    if len(coords) >= 2:
                        current_x += Decimal(coords[0])
                        current_y += Decimal(coords[1])
                        vertices.append((current_x, current_y))
                        i += 1
            
            elif cmd == 'Z' or cmd == 'z':
                vertices.append((start_x, start_y))
        else:
            i += 1
    
    if not vertices:
        return
    
    # Find bounding box
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    
    min_x_int = int(Decimal(min_x))
    max_x_int = int(Decimal(max_x))
    min_y_int = int(Decimal(min_y))
    max_y_int = int(Decimal(max_y))
    
    # Determine grid alignment
    x_frac = min_x % Decimal(1)
    y_frac = min_y % Decimal(1)
    
    x_is_standard = x_frac == 0 or x_frac - Decimal(0.5) == 0 or x_frac - Decimal(1) == 0
    y_is_standard = y_frac == 0 or y_frac - Decimal(0.5) == 0 or y_frac - Decimal(1) == 0
    
    if x_is_standard and y_is_standard:
        for iy in range(min_y_int, max_y_int + 1):
            for ix in range(min_x_int, max_x_int + 1):
                centers_to_test = [(Decimal(ix) + Decimal('0.5'), Decimal(iy) + Decimal('0.5'))]
                
                y_level = iy + Decimal(0.5)
                x_coords_at_y = []
                for idx in range(len(vertices)):
                    v1 = vertices[idx]
                    v2 = vertices[(idx + 1) % len(vertices)]
                    y1, y2 = v1[1], v2[1]
                    
                    if (y1 <= y_level <= y2) or (y2 <= y_level <= y1):
                        if abs(y2 - y1) > Decimal(0.001):
                            t = (y_level - y1) / (y2 - y1)
                            x_at_y = v1[0] + t * (v2[0] - v1[0])
                            x_coords_at_y.append(x_at_y)
                
                has_half_x_boundary = any(x % Decimal(1) - Decimal(0.5) == 0 for x in x_coords_at_y)
                
                x_level = ix + Decimal(0.5)
                y_coords_at_x = []
                for idx in range(len(vertices)):
                    v1 = vertices[idx]
                    v2 = vertices[(idx + 1) % len(vertices)]
                    x1, x2 = v1[0], v2[0]
                    
                    if (x1 <= x_level <= x2) or (x2 <= x_level <= x1):
                        if abs(x2 - x1) > Decimal(0.001):
                            t = (x_level - x1) / (x2 - x1)
                            y_at_x = v1[1] + t * (v2[1] - v1[1])
                            y_coords_at_x.append(y_at_x)
                
                has_half_y_boundary = any(y % Decimal(1) - Decimal(0.5) == 0 for y in y_coords_at_x)
                
                if has_half_x_boundary and not has_half_y_boundary:
                    centers_to_test = [(Decimal(ix), Decimal(iy) + Decimal('0.5'))]
                elif has_half_y_boundary and not has_half_x_boundary:
                    centers_to_test = [(Decimal(ix) + Decimal('0.5'), Decimal(iy))]
                elif has_half_x_boundary and has_half_y_boundary:
                    centers_to_test = [(Decimal(ix), Decimal(iy))]
                
                for center_x, center_y in centers_to_test:
                    if point_in_polygon(center_x, center_y, vertices):
                        tx, ty = transform.apply_point(center_x, center_y)
                        theta = transform.get_rotation(precision, square_id_counter[0])
                        
                        squares.append({
                            'id': square_id_counter[0],
                            'x': tx,
                            'y': ty,
                            'theta': theta
                        })
                        square_id_counter[0] += 1
    else:
        x_offset = min_x % Decimal(1)
        y_offset = min_y % Decimal(1)
        
        for iy in range(min_y_int, max_y_int + 1):
            for ix in range(min_x_int, max_x_int + 1):
                center_x = Decimal(ix) + x_offset + Decimal('0.5')
                center_y = Decimal(iy) + y_offset + Decimal('0.5')
                
                if point_in_polygon(center_x, center_y, vertices):
                    tx, ty = transform.apply_point(center_x, center_y)
                    theta = transform.get_rotation(precision, square_id_counter[0])
                    
                    squares.append({
                        'id': square_id_counter[0],
                        'x': tx,
                        'y': ty,
                        'theta': theta
                    })
                    square_id_counter[0] += 1


# Keep the original function for backward compatibility
def extract_squares_from_path(path_d, transform, squares, entities, square_id_counter, precision=50):
    """
    Extract squares from filled path patterns.
    Uses the new polygon-filling algorithm.
    """
    extract_squares_from_path_v2(path_d, transform, squares, entities, square_id_counter, precision)


def extract_single_region_from_path(path_d, transform, squares, entities, square_id_counter, precision=50):
    """
    Extract squares from a single-region filled path.
    Uses the new polygon-filling algorithm.
    """
    extract_single_region_v2(path_d, transform, squares, entities, square_id_counter, precision)


def process_element(element, transform, squares, entities, defs, square_id_counter, precision=50):
    """Recursively process SVG elements and extract unit squares"""
    
    # Get transform for this element FIRST
    transform_attr = element.get('transform', '')
    if transform_attr:
        elem_transform = parse_transform_attr(transform_attr, entities, precision)
        transform = transform.multiply(elem_transform)

    if use_parser_g:
        # Check for <parser:g> children - if found, process only those and skip siblings
        parser_children = [child for child in element if 'parser' in str(child.tag).lower()]
        if parser_children:
            for parser_elem in parser_children:
                for child in parser_elem:
                    process_element(child, transform.copy(), squares, entities, defs, square_id_counter, precision)
            return
    
    # Handle <use> elements
    if element.tag == '{http://www.w3.org/2000/svg}use':
        href = element.get('{http://www.w3.org/1999/xlink}href', '')
        if href.startswith('#'):
            ref_id = href[1:]
            if ref_id in defs:
                if 'fill:none' in element.get('style', ''):
                    return
                process_element(defs[ref_id], transform.copy(), squares, entities, defs, square_id_counter, precision)
    
    # Handle <rect> elements
    elif element.tag == '{http://www.w3.org/2000/svg}rect':
        if element.get('id') == 'outer':
            return
        
        width_str = element.get('width', '')
        height_str = element.get('height', '')
        x_str = element.get('x', '0')
        y_str = element.get('y', '0')
        style = element.get('style', '')
        
        width_str = replace_entities(width_str, entities)
        height_str = replace_entities(height_str, entities)
        x_str = replace_entities(x_str, entities)
        y_str = replace_entities(y_str, entities)
        
        if 'fill:none' in style:
            return
        
        try:
            width = int(float(width_str)) if width_str else 0
            height = int(float(height_str)) if height_str else 0
            rect_x = Decimal(x_str) if x_str else Decimal('0')
            rect_y = Decimal(y_str) if y_str else Decimal('0')
        except:
            width = 0
            height = 0
            rect_x = Decimal('0')
            rect_y = Decimal('0')
        
        for ix in range(width):
            for iy in range(height):
                center_x = rect_x + Decimal(ix) + Decimal('0.5')
                center_y = rect_y + Decimal(iy) + Decimal('0.5')
                x, y = transform.apply_point(center_x, center_y)
                theta = transform.get_rotation(precision, square_id_counter[0])
                
                squares.append({
                    'id': square_id_counter[0],
                    'x': x,
                    'y': y,
                    'theta': theta
                })
                square_id_counter[0] += 1
    
    # Handle <path> elements
    elif element.tag == '{http://www.w3.org/2000/svg}path':
        d = element.get('d', '')
        style = element.get('style', '')
        
        # Skip filled paths if parent already has <use> or <rect> elements for squares
        # (they represent the same squares redundantly)
        if d and 'fill:none' not in style:
            extract_squares_from_path(d, transform, squares, entities, square_id_counter, precision)
    
    # Recursively handle <g> elements
    elif element.tag == '{http://www.w3.org/2000/svg}g':
        for child in element:
            process_element(child, transform.copy(), squares, entities, defs, square_id_counter, precision)


def parse_svg(filename, precision=50):
    """Parse SVG file and extract all unit squares"""
    
    with open(filename, 'r') as f:
        svg_content = f.read()
    
    entities = parse_entities(svg_content)
    print(f"Parsed {len(entities)} entity definitions:")
    for name, value in entities.items():
        print(f"  {name} = {value}")
    
    if precision == 0:
        max_digits = 0
        for entity_value in entities.values():
            val_str = entity_value.strip()
            
            if val_str.startswith('-') or val_str.startswith('+'):
                val_str = val_str[1:]
            
            if '.' in val_str:
                parts = val_str.split('.')
                integer_part = parts[0].lstrip('0') or '0'
                decimal_part = parts[1].rstrip('0') if len(parts) > 1 else ''
                if integer_part == '0':
                    decimal_part_stripped = decimal_part.lstrip('0')
                    digit_count = len(decimal_part_stripped)
                else:
                    digit_count = len(integer_part) + len(decimal_part)
            else:
                val_str = val_str.lstrip('0') or '0'
                val_str = val_str.rstrip('0')
                digit_count = len(val_str)
            
            max_digits = max(max_digits, digit_count)
        
        precision = max(max_digits, 20)
        print(f"Auto-detected precision: {precision} digits")

    getcontext().prec = precision + 20
    
    svg_content_substituted = svg_content
    max_iterations = 10
    for iteration in range(max_iterations):
        old_content = svg_content_substituted
        for name, value in entities.items():
            svg_content_substituted = svg_content_substituted.replace(f'&{name};', value)
        if svg_content_substituted == old_content:
            break
    
    svg_content_clean = re.sub(r'<!DOCTYPE[^>]+\[.*?\]>', '', svg_content_substituted, flags=re.DOTALL)
    
    root = ET.fromstring(svg_content_clean)

    viewbox_centered = 'hs' in entities and root.get('viewBox', '') == f'-{entities["hs"]} -{entities["hs"]} {entities["s"]} {entities["s"]}'

    defs = {}
    
    for defs_elem in root.findall('.//{http://www.w3.org/2000/svg}defs'):
        for elem in defs_elem:
            elem_id = elem.get('id')
            if elem_id:
                defs[elem_id] = elem
    
    for elem in root.iter():
        elem_id = elem.get('id')
        if elem_id and elem_id not in defs:
            defs[elem_id] = elem
    
    print(f"Found {len(defs)} defined groups: {list(defs.keys())}", end="")
    
    squares = []
    square_id_counter = [1]
    
    base_transform = Transform()
    
    for child in root:
        if not child.tag == '{http://www.w3.org/2000/svg}defs':
            process_element(child, base_transform.copy(), squares, entities, defs, square_id_counter, precision)
    
    return squares, entities, precision, viewbox_centered


def save_txt(filename, squares, s_value, precision=50):
    """Save squares in CUDA optimizer format"""
    actual_precision = precision
    with open(filename, 'w') as f:
        f.write(f"Final s: {s_value}\n\n")
        pi_hp = hp_pi(actual_precision)
        for sq in squares:
            x = sq['x']
            y = sq['y']
            theta_rad = Decimal(str(sq['theta']))
            theta_deg = theta_rad * Decimal(180) / pi_hp
            
            f.write(f"Square {sq['id']}: x={x:.{precision}f}, y={y:.{precision}f}, deg={theta_deg:.{precision}f}\n")


def save_svg(filename, squares, s_value, precision=10):
    """Save SVG visualization"""
    
    with open(filename, 'w') as f:
        if squares:
            s = float(s_value)
            half_s = s / 2.0
        else:
            s = 1.0
            half_s = 0.5
        
        display_size = 800.0
        scale = display_size / s
        offset = display_size / 2.0
        
        text_x = 820.0
        text_y_start = 30.0
        line_height = 20.0
        
        text_lines = 1 + 1 + 1 + len(squares)
        
        total_text_height = text_y_start + (text_lines * line_height) + 20.0
        svg_height = max(display_size, total_text_height)
        
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{svg_height}" style="background-color: white;">\n')
        
        cont_px = s * scale
        f.write(f'<rect x="{offset - cont_px/2.0}" y="{offset - cont_px/2.0}" ')
        f.write(f'width="{cont_px}" height="{cont_px}" ')
        f.write(f'fill="none" stroke="red" stroke-width="0.1" />\n')
        
        for sq in squares:
            x = float(sq['x'])
            y = float(sq['y'])
            theta = float(sq['theta'])
            
            cx = offset + x * scale
            cy = offset - y * scale
            size_px = 1.0 * scale
            angle_deg = -theta * 180.0 / math.pi
            
            f.write(f'<rect x="{cx - size_px/2.0}" y="{cy - size_px/2.0}" ')
            f.write(f'width="{size_px}" height="{size_px}" ')
            f.write(f'fill="rgba(0,100,255,0.5)" stroke="black" stroke-width="0.1" ')
            f.write(f'transform="rotate({angle_deg} {cx} {cy})" />\n')
            
            font_size = min(15, size_px * 0.35)
            
            f.write(f'<text x="{cx}" y="{cy + font_size * 0.25}" ')
            f.write(f'font-family="Arial" font-size="{font_size}" text-anchor="middle" fill="black">')
            f.write(f'{sq["id"]}</text>\n')
        
        text_y = text_y_start
        f.write(f'<text x="{text_x}" y="{text_y}" ')
        f.write(f'font-family="Courier New" font-size="16" font-weight="bold">Result for N={len(squares)}</text>\n')
        text_y += 30.0
        
        s_display = float(s_value) if squares else 0.0
        f.write(f'<text x="{text_x}" y="{text_y}" ')
        f.write(f'font-family="Courier New" font-size="14">s = {s_display:.{precision}f}</text>\n')
        text_y += 30.0
        
        f.write(f'<text x="{text_x}" y="{text_y}" ')
        f.write(f'font-family="Courier New" font-size="12" font-weight="bold">Coordinates &amp; Angles:</text>\n')
        text_y += line_height
        
        for sq in squares:
            x = sq['x']
            y = sq['y']
            theta_rad = Decimal(str(sq['theta']))
            theta_deg = theta_rad * Decimal(180) / Decimal(str(math.pi))
            
            f.write(f'<text x="{text_x}" y="{text_y}" ')
            f.write(f'font-family="Courier New" font-size="12">')
            f.write(f'Square {sq["id"]}: x={x:.{precision}f}, y={y:.{precision}f}, deg={theta_deg:.{precision}f}</text>\n')
            
            text_y += line_height
        
        f.write('</svg>\n')


def calculate_s(squares):
    """Calculate enclosing square size from squares"""
    if not squares:
        return Decimal(0)
    
    max_s = Decimal(0)
    
    for sq in squares:
        x = sq['x']
        y = sq['y']
        theta = Decimal(str(sq['theta']))
        
        cos_theta = Decimal(str(hp_cos(theta)))
        sin_theta = Decimal(str(hp_sin(theta)))
        extent = (abs(cos_theta) + abs(sin_theta)) / Decimal(2)
        
        max_coord = max(abs(x) + extent, abs(y) + extent)
        
        max_s = max(max_s, max_coord)
    
    return max_s * Decimal(2)



if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 parse_svg_packing_v2.py <input.svg> <precision> [output.txt]")
        print("Example: python3 parse_svg_packing_v2.py square-301.svg 50 output.txt")
        print("         python3 parse_svg_packing_v2.py square-301.svg 0 output.txt  # auto-detect precision")
        sys.exit(1)
    
    input_file = sys.argv[1]
    precision = int(sys.argv[2])
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'output.txt'
    
    print(f"Parsing {input_file}...")
    squares, entities, actual_precision, viewbox_centered = parse_svg(input_file, precision)
    
    getcontext().prec = actual_precision + 20

    pi_hp = hp_pi(actual_precision)
    threshold = Decimal(10) ** (-(precision - 10)) if precision > 10 else Decimal("1e-6")
    
    for sq in squares:
        sq['theta'] = pi_hp/Decimal(2) - sq['theta']
        
        if abs(sq['theta']) < threshold:
            sq['theta'] = Decimal(0)
        elif abs(sq['theta'] - pi_hp/Decimal(2)) < threshold:
            sq['theta'] = pi_hp/Decimal(2)
        elif abs(sq['theta'] + pi_hp/Decimal(2)) < threshold:
            sq['theta'] = -pi_hp/Decimal(2)
        elif abs(sq['theta'] - pi_hp) < threshold:
            sq['theta'] = pi_hp
        elif abs(sq['theta'] + pi_hp) < threshold:
            sq['theta'] = -pi_hp
        
        sq['theta'] = (sq['theta'] + pi_hp) % (pi_hp/Decimal(2))
    
    print(f"\nExtracted {len(squares)} squares")
    
    if squares:
        s_value = Decimal(entities['s'])
        
        half_s = s_value / Decimal(2)
        if viewbox_centered:
            half_s = 0
        for sq in squares:
            sq['x'] = (sq['x'] - half_s)
            sq['y'] = -(sq['y'] - half_s)
        
        svg_file = output_file.rsplit('.', 1)[0] + '.svg'
        print(f"Saving SVG to {svg_file}...")
        save_svg(svg_file, squares, s_value, precision=10)
    
    print(f"Saving to {output_file}...")
    save_txt(output_file, squares, s_value, actual_precision)
    
    print("Done!")
