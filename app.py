from flask import Flask, render_template, request
import networkx as nx
import osmnx as ox
import folium as flm
from folium.features import DivIcon

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

app = Flask(__name__)
app.vars = {}
bos_graph = nx.read_gpickle('BostonGraph_reduced.gpickle')

@app.route('/index',methods=['GET', 'POST'])
def index():
    cLocation = 'here'
    tLocation = 'there'
    if request.method == 'GET':
        return render_template('index.html',cL=cLocation,tL=tLocation)
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

        oroute_list = find_route(node1, node2, bos_graph)
        routeInfo = route_info(oroute_list, bos_graph)        
        save_route_html(oroute_list, bos_graph, cCoord, tCoord)
        
        return render_template('route.html',cL=app.vars['currentL'],tL=app.vars['targetL'], fr_distance=int(routeInfo[0]), fr_nlight=routeInfo[1], br_distance=int(routeInfo[2]), br_nlight=routeInfo[3])


@app.route('/next_route',methods=['POST'])
def next_route():  #remember the function name does not need to match the URL
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
    
    oroute_list = find_route(node1, node2, bos_graph)
    routeInfo = route_info(oroute_list, bos_graph)
    save_route_html(oroute_list, bos_graph, cCoord, tCoord)
    return render_template('route.html',cL=app.vars['currentL'],tL=app.vars['targetL'], fr_distance=int(routeInfo[0]), fr_nlight=routeInfo[1], br_distance=int(routeInfo[2]), br_nlight=routeInfo[3])


def find_route(start, target, graph):
    fastest_route = nx.dijkstra_path(graph, start, target, weight='length')
    brighter_route = nx.dijkstra_path(graph, start, target, weight='length_SL_density')        
    return [fastest_route, brighter_route]


def route_info(routes, graph):
    route_info = []
    for route in routes:
        u = route[0]
        totalDist=0
        totalSL=0
        for v in route[1:]:
            totalDist += graph[u][v][0]['length']
            totalSL += graph[u][v][0]['SL_count']    
            u = v
        route_info.append(totalDist)
        route_info.append(totalSL)
    return route_info


def address_to_coord(addr):
    geolocator = Nominatim(user_agent="app", timeout=10)
    try:
        location = geolocator.geocode(addr)
    except GeocoderTimedOut:
        return address_to_coord(addr)
    return (location.latitude, location.longitude)


def save_route_html(route_list, graph, oCoord, dCoord):
    print("save_route_html")
    map = flm.Map(
        location=[42.361145, -71.057083],
        tiles='cartodbpositron',
        zoom_start=13
    )
    
    locationlist = [oCoord, dCoord]
    popup_list = ['Origin','Destination']
    string = ['Origin','Destination']

    for point in range(0, len(locationlist)):
        flm.Marker(locationlist[point], popup=popup_list[point], tooltip=string[point]).add_to(map)
        
    route_graph_map = ox.plot_route_folium(graph, route_list[1], route_map=map, route_color='#ffff00', route_opacity=1, route_width=3)    
    route_graph_map = ox.plot_route_folium(graph, route_list[0], route_map=map, route_color='#808080', route_opacity=1, route_width=1)
    route_graph_map.save('templates/route_graph_test.html')

    # with is like your try .. finally block in this case
    with open('templates/route_graph_test.html', 'rt') as file:
        with open('templates/route_graph_test_adjusted.html', 'wt') as fout:
            for idx, line in enumerate(file):
                if(idx == 27):
                    line=line.replace('100','75')
                if(idx==28):
                    line=line.replace('100','90')                
                if(idx == 29):
                    line=line.replace('0.0','28.0')
                fout.write(line)
            fout.close()
        file.close()
    

if __name__ == '__main__':
    app.run(debug=True)
