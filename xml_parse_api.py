import cdcs
from cdcs import CDCS
import pandas as pd
import xml.dom.minidom as md

curator = CDCS('https://portal.meta-genome.org/', username='')
template="mecha-metagenome-schema31"        # Make this to not have to be hard-coded
query_dict = "{\"map.metamaterial-material-info\": {\"$exists\": true}}"
my_query= curator.query(template=template, mongoquery=query_dict)
xml_content = my_query.iloc[0].xml_content


class xml_control:
    def __init__(self, xml_string):
        self.xml_string = xml_string
    
    
    def inspect_xml_api(self, keyword):
        import xml.etree.ElementTree as ET
        data_type = keyword

        

        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        root_elems = []
        for child in root.findall("./*"):
            root_elems.append(child)

        # submission type - base/meta
        submission_type = root_elems[3].tag
        words = submission_type.split('-')
        sub_type = '-'.join(words[:-1])
        
        measure_val_units = {}
        measure_val_units["submission_type"] = sub_type
        measure_values = {}
        measure_units = {}
        values = {}
        measure_vals_units_list = []
        #print(sub_type)

        if sub_type == "component":
            values = {"values" : {keyword: None}}
            measure_units = {"units": None}
            measure_vals_units_list = [values, measure_units]
            measure_val_units[keyword] = measure_vals_units_list
            measure_val_units["sensitivity"] = "compoent"

            return measure_val_units
            
        else:
            type_elems = []
            for child in root_elems[3]:
                type_elems.append(child)

            # chosen directional sensitivity
            sensitivity = type_elems[-1].tag
            words = sensitivity.split('-')
            sensitivity_type = '-'.join(words[:-1])

            #sensitivity = ['-'.join(word.split('-')[:-1]) for word in sensitivity]

            avail_sensitivity = {"isotropic-choice":"-iso",
                                "transversely-isotropic-choice": "-trans",
                                "orthotropic-choice" : "-ortho",
                                "component-test-data": "component"}
            
            sensitivity_sufix = avail_sensitivity[type_elems[-1].tag]
            # getting single point values and units
            

                
            if keyword == "bulk-density":
                
                bulk_density = root.findall(f"./{submission_type}/bulk-density")
                bulk_density_units = root.findall(f"./{submission_type}/bulk-density-unit")
                #print(bulk_density)
                values = {"values" : {"bulk-density": bulk_density[0].text}}
                
                #print(values)
                measure_units = {"units": bulk_density_units[0].text}
                #print(measure_units)
                measure_vals_units_list = [values, measure_units]
                measure_val_units["bulk-density"] = measure_vals_units_list
                measure_val_units["sensitivity"] = sensitivity_type

                return measure_val_units

            elif keyword != "bulk-density":

                choice_elems = []
                for child in type_elems[-1]:
                    choice_elems.append(child.tag)
                    #print(child.tag.split('-').pop(-1))

                # all properties in directional sensitivity
                choice_elems_clean = ['-'.join(word.split('-')[:-1]) for word in choice_elems]

                # Getting single measures only - i.e. tensile modulus etc.
                identified_data = []
                
                for clean_elem in choice_elems_clean:
                    #print(clean_elem)
                    if clean_elem == data_type:
                        identified_data.append(clean_elem)

                # identified single point properties within this submission:"""

                #print(identified_properties)

                

                # loop over requested measures
                if not identified_data:
                    
                    measure_units["units"] = None
                    values["values"] = None
                    
                    measure_vals_units_list = [values, measure_units]
                    measure_val_units[keyword] = measure_vals_units_list
                else:
                    for elem in identified_data:
                        # get list of xml objects at requested measure level  
                        branch = root.findall(f"./{submission_type}/{sensitivity}/{elem + sensitivity_sufix}/*")
                        # get units
                        units = [word for word in branch if 'unit' in word.tag]
                        # remove all that contain 'conditions' and unit keyword
                        val = [word for word in branch if 'conditions' not in word.tag and 'unit' not in word.tag]
                    
                        for element in val:
                            measure_values[element.tag] = element.text
                        values["values"] = measure_values
                        if units:
                            for element in units:
                                measure_units["units"] = element.text
                        else:
                            measure_units["units"] = None
                        measure_vals_units_list = [values, measure_units]
                        measure_val_units[elem] = measure_vals_units_list
                
                # getting all single point values into organised dictionary
                # print(measure_val_units)
                measure_val_units["sensitivity"] = sensitivity_type
            
                
                return measure_val_units
    


    def get_topologies(self):
        import xml.etree.ElementTree as ET
        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        root_elems = []
        for child in root.findall("./*"):
            root_elems.append(child)

        # submission type
        submission_type = root_elems[3].tag
        
        type_elems = []
        for child in root_elems[3]:
            type_elems.append(child)

        # chosen directional sensitivity
        sensitivity = type_elems[-1].tag
        # dict to contain each continuous measure set of topologies and unit-cell
        measure_topols = {}
        # list of all topology files for unit cell
        unit_cell_topols = [element.find("./topology-url").text for element in root_elems[3] if 'topol' in element.tag]
        #insert unit cell topologies into topologies dict
        measure_topols["unit-cell-topologies"] = unit_cell_topols

        # all measured properties in submission from choice level
        choice_elems = []
        for child in type_elems[-1]:
            choice_elems.append(child)
            print(child.tag.split('-').pop(-1))

        possible_data = ['stress-strain', 'trans-axial-strain', 'base-stress-relax', 'base-twist-axial-strain']

        # slice to only get continuous measures by keyword search - accounts for variety in phasing
        identified_properties = []
        for elem in choice_elems:
            for data_type in possible_data:
                if data_type in elem.tag:
                    identified_properties.append(elem)
        
        for j, elem in enumerate(identified_properties):
            # get all elems in continuous data:
            continuous_type = root.findall(f"./{submission_type}/{sensitivity}/{elem.tag}/*")
            # get all topology uploads
            topologies = [element for element in continuous_type if 'topology' in element.tag]
            # dict for individual measure topologies
            grouped_topols ={}
            for i, element in enumerate(topologies):
                topol_urls = element.find("./topology-url").text
                grouped_topols[element.tag + "-" + str(i)] = topol_urls
            measure_topols[elem.tag + "-" + str(j)] = grouped_topols
    
        return measure_topols

    def interactive_expansion(self):
        dom = md.parseString(self.xml_string)

        # Print the available elements to the console
        print("Available elements:")
        root_elem = dom.documentElement
        for i, elem in enumerate(root_elem.childNodes):
            if elem.nodeType == md.Node.ELEMENT_NODE:
                print(f"{i}: {elem.tagName}")

        def recur_select(recur_index, recur_elem):
            print(recur_index)
            if recur_index >= 0:
                elems = recur_elem.childNodes[recur_index]
                print(f"\nContents of {elems.tagName}:")
                for j, child in enumerate(elems.childNodes):
                    #if child.nodeType == md.Node.ELEMENT_NODE:
                    if child.nodeType == md.Node.ELEMENT_NODE:
                        print(f"{j}: {child.tagName}")
                    elif child.nodeType == md.Node.TEXT_NODE:
                        print(f"{j}: {child.nodeValue}")
                    
                new_index = int(input("Enter the index of the element to expand (or -1 to go to root level):"))                
                return recur_select(new_index, elems)
            
            if recur_index < 0:
                root_elem = dom.documentElement
                for i, elem in enumerate(root_elem.childNodes):
                    if elem.nodeType == md.Node.ELEMENT_NODE:
                        print(f"{i}: {elem.tagName}")
                
                new_index = int(input("Enter the index of the element to expand (or -1 to go exit):")) 
                if new_index < 0:
                    
                    return (-1)
                else:
                    
                    return recur_select(new_index, root_elem)
        
        # Get user input for which element to expand
        elem_index = int(input("Enter the index of the element to expand (or -1 to exit): "))
            
        while elem_index >= 0:
            # Get the selected element
            elem = root_elem.childNodes[elem_index]

            # Print the contents of the selected element
            print(f"\nContents of {elem.tagName}:")
            for j, child in enumerate(elem.childNodes):
                #if child.nodeType == md.Node.ELEMENT_NODE:
                print(f"{j}: {child.tagName}")

            # Get user input for which child element to expand
            child_index = int(input("Enter the index of the child element to expand (or -1 to go back): "))
            elem_index  = recur_select(child_index, elem)


    def print_publication_details_api(self):
        import xml.etree.ElementTree as ET
        
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        root = tree.getroot()

        # Extract the relevant information
        authors = ', '.join([f"{au.find('author-initials').text} {au.find('author-surname').text}" for au in root.findall('.//publication-authors')])
        title = root.find('.//publication-title').text
        journal = root.find('.//publication-journal').text
        year = root.find('.//publication-year').text
        doi = root.find('.//id').text
        image_url_elem = root.find('.//image-url')
        meta_pid = root.find('./developer-section/pid').text 
        print(meta_pid)
        if image_url_elem is not None:
            uc_img = image_url_elem.text
        else:
            uc_img = None
        # Create the JSON variable
        data = {'authors': authors, 'title': title, 'journal': journal, 'year': year, 'doi': doi, "img": uc_img, "metaPid" : meta_pid}
        #print(data)

        # Print the JSON variable
        
        return data

    def find_sub_elem(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.xml_string)
        print(root)
        rows = root.find('.//xls-upload-stress-strain-table/rows')
        for row in rows.findall('row'):
            # Get the values of the columns in the row
            values = [c.text for c in row.findall('column')]
            # Print the values
            #print(values)
    
    def get_base_stress_strain(self):
        import xml.etree.ElementTree as ET

        # parse the XML string
        tree = ET.ElementTree(ET.fromstring(self.xml_string))

        # get the root element
        root = tree.getroot()
        base_tree = root.findall("./base-material-info")
        base_count = len(base_tree)
        #print(base_count)
        base_dict = {}
        for i in range(base_count):
            base_stress_strain = root.findall(f"./base-material-info/isotropic-choice/base-stress-strain")
            base_stress_strain_count = len(base_stress_strain)
            
            base_stress_strain_dict = {}
            for j in range(base_stress_strain_count):
                base_stress_strain_indiv = root.findall(f"./base-material-info[{i+1}]/isotropic-choice/base-stress-strain[{j+1}]/stress-strain-xls/xls-upload-stress-strain-table/rows/row")
                all_columns = []
                #print(j)
                for row in base_stress_strain_indiv:
                    all_columns.append([row[0].text, row[1].text])
                
                base_stress_strain_dict[f"stress_strain_{j}"] = all_columns
            
        base_dict[f"base_material_{i}"] = base_stress_strain_dict
        
    
#my_parse = xml_control(my_query, xml_content) 
#my_vals = my_parse.inspect_xml_api()
#print(my_vals)
#my_topols = my_parse.get_topologies()
#print(my_topols)
#my_parse.interactive_expansion()
#my_parse.print_publication_details()
#my_parse.find_sub_elem()
#my_parse.get_base_stress_strain()