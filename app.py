import json
from geojson import Point, Feature
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

import requests
import networkx as nx
import osmnx as ox
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import os

app = Flask(__name__)
app.vars = {}
bos_graph = nx.read_gpickle('BostonGraph.gpickle')

MAPBOX_ACCESS_KEY = 'pk.eyJ1IjoiamFrZWpieWkiLCJhIjoiY2s2Y2VneTJjMTNxZTNtbjhuanNjeGkyciJ9.b0pkKSJC5sHWrwXENm46KA'


@app.route('/index',methods=['GET','POST'])
def index():
    cLocation = 'here'
    tLocation = 'there'
    if request.method == 'GET':
        return render_template('index.html', 
            ACCESS_KEY=MAPBOX_ACCESS_KEY,
            f_route_data=None,
            s_route_data=None,
            route_start=None,
            route_end=None,            
            )            
    else:
        app.vars['currentL'] = request.form['current_location']
        app.vars['targetL'] = request.form['target_location'] 
               
        print(app.vars['currentL'])
        print(app.vars['targetL'])

        cCoord = address_to_coord(app.vars['currentL'])
        tCoord = address_to_coord(app.vars['targetL'])

        node1=ox.get_nearest_node(bos_graph,cCoord)
        node2=ox.get_nearest_node(bos_graph,tCoord)        

        print("node1 : ", node1)
        print("node2 : ", node2)

        o_routes = find_route(node1, node2, bos_graph)
        routeInfo = route_info(o_routes, bos_graph)   
        o_routes_Geo = find_route_in_Geo(node1, node2, bos_graph)
        centerP = o_routes_Geo[0][int(len(o_routes_Geo[0])/2)]                            
        print(o_routes_Geo[0][0], o_routes_Geo[0][-1])
        return render_template('route.html', 
            ACCESS_KEY=MAPBOX_ACCESS_KEY,
            f_route_data=o_routes_Geo[0],
            route_start = o_routes_Geo[0][0],
            route_end = o_routes_Geo[0][-1],
            s_route_data=o_routes_Geo[1],            
            cL=app.vars['currentL'],tL=app.vars['targetL'], incTime=int((0.85/60)*(routeInfo[4]-routeInfo[0])),
            f_distance=round(routeInfo[0]*0.000621371, 2), f_nlight=routeInfo[1], f_nCrime=routeInfo[2], f_nAccid=routeInfo[3], 
            s_distance=round(routeInfo[4]*0.000621371, 2), s_nlight=routeInfo[5], s_nCrime=routeInfo[6], s_nAccid=routeInfo[7],
            center=centerP
        )   

@app.route('/next_route',methods=['GET','POST'])
def next_route():
    cLocation = 'here'
    tLocation = 'there'
    if request.method == 'GET':
        return render_template('index.html', 
            ACCESS_KEY=MAPBOX_ACCESS_KEY,
            f_route_data=None,
            s_route_data=None,
            route_start=None,
            route_end=None,                        
            )
    else:
        app.vars['currentL'] = request.form['current_location']
        app.vars['targetL'] = request.form['target_location'] 
               
        print(app.vars['currentL'])
        print(app.vars['targetL'])

        cCoord = address_to_coord(app.vars['currentL'])
        tCoord = address_to_coord(app.vars['targetL'])

        node1=ox.get_nearest_node(bos_graph,cCoord)
        node2=ox.get_nearest_node(bos_graph,tCoord)        

        print("node1 : ", node1)
        print("node2 : ", node2)

        o_routes = find_route(node1, node2, bos_graph)
        routeInfo = route_info(o_routes, bos_graph)
        o_routes_Geo = find_route_in_Geo(node1, node2, bos_graph) 
        centerP = o_routes_Geo[0][int(len(o_routes_Geo[0])/2)]                            
        print(o_routes_Geo[0][0], o_routes_Geo[0][-1])
        return render_template('route.html', 
            ACCESS_KEY=MAPBOX_ACCESS_KEY,
            f_route_data=o_routes_Geo[0],
            s_route_data=o_routes_Geo[1],
            route_start = o_routes_Geo[0][0],
            route_end = o_routes_Geo[0][-1],                        
            cL=app.vars['currentL'],tL=app.vars['targetL'], incTime=int((0.85/60)*(routeInfo[4]-routeInfo[0])),
            f_distance=round(routeInfo[0]*0.000621371, 2), f_nlight=routeInfo[1], f_nCrime=routeInfo[2], f_nAccid=routeInfo[3],
            s_distance=round(routeInfo[4]*0.000621371, 2), s_nlight=routeInfo[5], s_nCrime=routeInfo[6], s_nAccid=routeInfo[7], center=centerP)   

def find_route(start, target, graph):
    f_route = nx.dijkstra_path(graph, start, target, weight='length')
    s_route = nx.dijkstra_path(graph, start, target, weight='length_21')        
    return [f_route, s_route]


def find_route_in_Geo(start, target, graph):
    fastest_route = nx.dijkstra_path(graph, start, target, weight='length')
    safe_route = nx.dijkstra_path(graph, start, target, weight='length_21')
    outlist = []
    f_route_list = []        
    s_route_list = []            
    for idx in range(0, len(fastest_route)):
        f_route_list.append([bos_graph.nodes[fastest_route[idx]]['x'], bos_graph.nodes[fastest_route[idx]]['y']])
    for idx in range(0, len(safe_route)):
        s_route_list.append([bos_graph.nodes[safe_route[idx]]['x'], bos_graph.nodes[safe_route[idx]]['y']])
    outlist.append(f_route_list)
    outlist.append(s_route_list)    
    return outlist


def route_info(i_routes, graph):
    route_info_list = []
    for route in i_routes:
        u = route[0]
        totalDist=0
        totalSL=0
        totalCrime=0
        totalAccid=0
        for v in route[1:]:
            totalDist += graph[u][v][0]['length']
            totalSL += graph[u][v][0]['SL_Count']    
            totalCrime += graph[u][v][0]['Crime_Count']                
            totalAccid += graph[u][v][0]['PED_Acci']                            
            u = v
        route_info_list.append(totalDist)
        route_info_list.append(totalSL)
        route_info_list.append(totalCrime)
        route_info_list.append(totalAccid)

    return route_info_list


def address_to_coord(addr):
    geolocator = Nominatim(user_agent="app", timeout=10)
    try:
        location = geolocator.geocode(addr)
    except GeocoderTimedOut:
        return address_to_coord(addr)
    return (location.latitude, location.longitude)

if __name__ == '__main__':
    app.run(debug=True) 
