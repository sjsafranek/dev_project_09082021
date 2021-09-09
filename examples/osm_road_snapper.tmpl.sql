-----------------------
-- JOIN TO OSM ROADS --
-----------------------

-- Description
-- High volume PostGIS template for finding the closest OSM road
-- to a given GPS waypoint for connected vehicles.

-- For some reason this isn't getting removed...
DROP TABLE IF EXISTS tmp_roads;

-- Create tmp table of waypoints of interest
CREATE TEMPORARY TABLE tmp_roads AS (
    SELECT
        -- grab the first timestamp for that lat lng journey combination. Ephemeris will do the rest
        wd.event_timestamp,
        wd.device_id,
        wd.heading,
        ST_SetSRID(ST_MakePoint(wd.longitude, wd.latitude), 4326) AS geom
    FROM
        road_snapping_source_events AS wd
    WHERE   wd._rowid >= %v         -- These values are feed into the template from a GoLang script
        AND wd._rowid <  %v         -- These values are feed into the template from a GoLang script
);

-- Set geom SRID
ALTER TABLE tmp_roads
    ALTER COLUMN geom TYPE geometry(POINT, 4326)
        USING ST_SetSRID(geom,4326);

-- Build an index for the KNN operation
CREATE INDEX tmp_roads__geom_idx
    ON tmp_roads
    USING GIST (geom);

-- Determine bounding box of road segment features
WITH bbox AS (
    SELECT
        -- buffer by meters
        ST_Transform(
            ST_Buffer(
                ST_Transform(
                    ST_SetSRID(
                        ST_Extent(the_geom),
                        4326
                    ),
                3857),
                100
            ),
        4326) AS geom
    FROM ways
)
INSERT INTO road_snapping_segment_events (
    event_timestamp,
    device_id,
    osmid,
    highway,
    distance_from_road
)
SELECT
    c.event_timestamp,
    c.device_id,
    -- unpack the road data
    c.metadata->>'osm_id',
    c.metadata->>'class',
    (c.metadata->>'distance_from_road')::REAL
FROM (
    SELECT
        wd.event_timestamp,
        wd.device_id,
        (
            SELECT
                -- this needs to return a single column
                json_build_object(
                    'osm_id',
                    ways.osm_id,
                    'name',
                    ways.name,
                    'class',
                    classes.name,
                    'distance_from_road',
                    ST_DistanceSphere(
                        ST_SetSRID(ways.the_geom, 4326),
                        wd.geom
                    )::VARCHAR
                ) AS metadata
            FROM
                ways AS ways
            LEFT JOIN osm_way_classes AS classes
                ON classes.class_id = ways.class_id
            WHERE

                -- create a 20 meter bounding box around the waypoint point to check
                -- only check road segments that intersect with that bounding box
                ways.the_geom &&
                    ST_Envelope(
                        ST_Transform(
                            ST_Buffer(
                                ST_Transform(wd.geom, 3857),
                                20 -- meters
                            ),
                        4326)
                    )

                -- filter by heading of the road
                AND (

					-- TODO calculate_weighted_heading_of_linestring
					-- Precaculate heading a head of time so we are just comparing numbers...
                    wd.heading - (ST_Azimuth(ST_MakePoint(ways.x1, ways.y1), ST_MakePoint(ways.x2, ways.y2) ) / (2*pi())*360)::INTEGER BETWEEN -20 AND 20

                    -- Handle headings near 360...
                    -- Road heading 340 to 360, Record heading is 0 to 20
                    OR (wd.heading + 360) - (ST_Azimuth(ST_MakePoint(ways.x1, ways.y1), ST_MakePoint(ways.x2, ways.y2) ) / (2*pi())*360)::INTEGER BETWEEN -20 AND 20

					-- Road heading 0 to 20, Record heading is 340 to 360
                    OR wd.heading - ((ST_Azimuth(ST_MakePoint(ways.x1, ways.y1), ST_MakePoint(ways.x2, ways.y2) ) / (2*pi())*360)::INTEGER + 360) BETWEEN -20 AND 20
                )

            -- run the KNN operation
            ORDER BY ST_SetSRID(ways.the_geom, 4326) <-> wd.geom
            LIMIT 1
        )
        FROM
            tmp_roads AS wd

        -- select only waypoints that are near our road segment features
        INNER JOIN bbox
            ON ST_Contains(bbox.geom, wd.geom)

) AS c;
