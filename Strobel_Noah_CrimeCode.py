# Name: Noah Strobel

# Class: GISc-450

# Created: 3/31/2021

# This script imports shapefiles, creates a GDB entitled 'Strobel_Crime.gdb,
# moves those shapefiles to the newly-created GDB, and then projects them into
# NAD_1983_StatePlane_Virginia_North. It then prints the shapefile info (feature type)
# and then creates Thiessen polygons based on crime points. Finally, it counts the
# number of addresses in the Thiessen polygons and crime points in police beats
# and then exports that data to a CSV file


import arcpy
import os
import time

arcpy.env.overwriteOutput = True

time_start = time.time()


def main():

    print("\n\nThis scipt imports shapefiles, creates a GDB entitled 'Strobel_Crime.gdb,")
    print("moves the shapefiles to the GDB, and then re-projects them into")
    print("NAD_1983_StatePlane_Virginia_North. It then prints the shapefile info,")
    print("creates Thiessen polygons based on crime points, and counts the number of")
    print("addresses in those polygons and the number of crimes committed in police beats.")
    print("Finally, it creates CSV files of counted addresses and crimes in beats.")

    print("\n---Script Starting---")

    # Reading in the shapefiles

    boundary_shp = r"C:\GISc450\ArcPy3_Crime\data\FburgBoundary.shp"
    crime_data_shp = r"C:\GISc450\ArcPy3_Crime\data\FredCrimeData2.shp"
    police_beats_shp = r"C:\GISc450\ArcPy3_Crime\data\PoliceBeats.shp"
    centerlines_shp = r"C:\GISc450\ArcPy3_Crime\data\RoadCenterlines.shp"
    address_shp = r"C:\GISc450\ArcPy3_Crime\data\SiteAddresses.shp"

    # Defining the workspace

    workspace = r"C:\GISc450\ArcPy3_Crime"
    gdb_out = "Strobel_Crime.gdb"
    gdb_out_location = os.path.join(workspace, gdb_out)

    # If the GDB exists already, it will be deleted and over-written

    if arcpy.Exists(gdb_out_location):
        arcpy.Delete_management(gdb_out_location)
        if arcpy.Exists(gdb_out_location):
            print("\n---GDB not deleted---")
        else:
            print(f"\n---{gdb_out} created via the path {gdb_out_location}---")

    # Reading in the FburgCrimeReportXY CSV table

    FburgCrimeReportXY = r"C:\GISc450\ArcPy3_Crime\data\FburgCrimeReportXY.csv"

    # Describing the boundary feature class's projection

    boundary_desc = arcpy.Describe(boundary_shp)
    projection = boundary_desc.SpatialReference

    print(f"\nProjection of the boundary feature is {projection.name}")

    # Creating the GDB

    arcpy.CreateFileGDB_management(workspace, gdb_out)

    # Defining the workspace as the new GDB

    arcpy.env.workspace = r"C:\GISc450\ArcPy3_Crime\Strobel_Crime.gdb"

    # Exporting the shapefiles into the Strobel_Crime GDB

    arcpy.FeatureClassToFeatureClass_conversion(boundary_shp, gdb_out_location, "Boundary_shp")
    arcpy.FeatureClassToFeatureClass_conversion(crime_data_shp, gdb_out_location, "Crime_data_shp")
    arcpy.FeatureClassToFeatureClass_conversion(police_beats_shp, gdb_out_location, "Police_beats_shp")
    arcpy.FeatureClassToFeatureClass_conversion(centerlines_shp, gdb_out_location, "Centerlines_shp")
    arcpy.FeatureClassToFeatureClass_conversion(address_shp, gdb_out_location, "Address_shp")
    arcpy.TableToTable_conversion(FburgCrimeReportXY, gdb_out_location, "FburgCrimeData")

    fc_list = arcpy.ListFeatureClasses()

    arcpy.XYTableToPoint_management(FburgCrimeReportXY, "FburgCrimeData")
    print(f"\nFburgCrimeReportXY converted to a point feature class and extracted to {gdb_out}")
    print(f"under the name 'FburgCrimeData'")

    project_count = 0

    # Using a for loop to describe the feature classes

    for features in fc_list:
        desc = arcpy.Describe(features)
        shape_type = desc.shapeType
        fc_name = desc.name

        print(f"\n{fc_name} extracted to {gdb_out}")
        print(f"{fc_name} is a {shape_type} feature")

        # Projecting the feature classes to NAD_1983_StatePlane_Virginia_North

        reproject_name = fc_name.strip(".shp") + "Project"
        new_projection = arcpy.SpatialReference(2283)
        arcpy.Project_management(features, reproject_name, new_projection)
        arcpy.Project_management("FburgCrimeData", "FburgCrimeData_Project", new_projection)
        project_count += 1

    print(f"\n{project_count} files projected to {new_projection.name}")

    # Making the boundary polyline a polygon feature

    arcpy.FeatureToPolygon_management("Boundary_Project", "Boundary_project_poly")

    # Describing the police beat feature's catalog path

    police_beats_desc = arcpy.Describe("Police_beats_shp")
    catalog_path = police_beats_desc.catalogPath
    print(f"\nPolice beats catalog path is {catalog_path}")

    # Creating Thiessen polygons based on the crime points

    arcpy.CreateThiessenPolygons_analysis("Crime_data_shp", "Crime_data_thiessen", "ALL")
    arcpy.Clip_analysis("Crime_data_thiessen", "Boundary_project_poly", "Crime_thiessen_clip")

    thiessen_describe = arcpy.Describe("Crime_thiessen_clip")
    thiessen_catalog_path = thiessen_describe.catalogPath

    print(f"\nThiessen polygons have been created in {thiessen_catalog_path} and clipped to")
    print("the Fredericksburg boundary polygon")

    # Finally, writing CSV files for the Thiessen polygon and police beat features

    thiessen_csv_out = "Strobel_Noah_ThiessenCSV.csv"

    if arcpy.Exists(thiessen_csv_out):
        arcpy.Delete_management(thiessen_csv_out)

    arcpy.SummarizeWithin_analysis("Crime_thiessen_clip", "Address_Project", "addresses_in_thiessen_clip")
    arcpy.TableToTable_conversion("addresses_in_thiessen_clip", workspace, thiessen_csv_out)

    print("\nThe table for address points within the thiessen polygons has been created and named")
    print(f"{thiessen_csv_out}")

    police_beat_csv_out = "Strobel_Noah_BeatsCSV.csv"

    if arcpy.Exists(police_beat_csv_out):
        arcpy.Delete_management(police_beat_csv_out)

    arcpy.SummarizeWithin_analysis("Police_beats_Project", "Crime_data_Project", "police_beats_table")
    arcpy.TableToTable_conversion("police_beats_table", workspace, police_beat_csv_out)

    print("\nThe table for the number of crimes within police beats has been created and named")
    print(f"{police_beat_csv_out}")


if __name__ == '__main__':
    main()

time_end = time.time()
total_time = time_end - time_start
minutes = int(total_time / 60)
seconds = total_time % 60
print(f"\nThe script finished in {minutes} minutes {int(seconds)} seconds")
