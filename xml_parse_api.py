from cdcs import CDCS
import pandas as pd
import xml.dom.minidom as md
import xml.etree.ElementTree as ET

#curator = CDCS('https://portal.meta-genome.org/', username='')
#template="mecha-metagenome-schema31"        # Make this to not have to be hard-coded
#query_dict = "{\"map.metamaterial-material-info\": {\"$exists\": true}}"
#my_query= curator.query(template=template, mongoquery=query_dict)
#xml_content = my_query.iloc[0].xml_content


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


            avail_sensitivity = {"isotropic-choice":"-iso",
                                "transversely-isotropic-choice": "-trans",
                                "orthotropic-choice" : "-ortho",
                                "component-test-data": "component"}
            
            sensitivity_sufix = avail_sensitivity[type_elems[-1].tag]
            # getting single point values and units
            

                
            if keyword == "bulk-density":
                
                bulk_density = root.findall(f"./{submission_type}/bulk-density")
                bulk_density_units = root.findall(f"./{submission_type}/bulk-density-unit")

                values = {"values" : {"bulk-density": bulk_density[0].text}}
                
                measure_units = {"units": bulk_density_units[0].text}
                measure_vals_units_list = [values, measure_units]
                measure_val_units["bulk-density"] = measure_vals_units_list
                measure_val_units["sensitivity"] = sensitivity_type

                return measure_val_units

            elif keyword != "bulk-density":

                choice_elems = []
                for child in type_elems[-1]:
                    choice_elems.append(child.tag)

                # all properties in directional sensitivity
                choice_elems_clean = ['-'.join(word.split('-')[:-1]) for word in choice_elems]

                # Getting single measures only - i.e. tensile modulus etc.
                identified_data = []
                
                for clean_elem in choice_elems_clean:
                    if clean_elem == data_type:
                        identified_data.append(clean_elem)

                # identified single point properties within this submission:"""

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
                measure_val_units["sensitivity"] = sensitivity_type
            
                
                return measure_val_units
    

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
        
        return data

    