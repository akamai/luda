package regexrunner;

import java.io.FileWriter;
import java.io.IOException;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;



import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.FileReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Iterator;
public class JsonOperation {

	
		
		public static ArrayList<String> read(String jsonPath) throws IOException, ParseException {

    		ArrayList<String> result = new ArrayList<String>();

	        JSONParser parser = new JSONParser();
	        Reader reader = new FileReader(jsonPath);

	            JSONObject jsonObject = (JSONObject) parser.parse(reader);


	            // loop array
	            JSONArray msg = (JSONArray) jsonObject.get("to_test");
	            Iterator<String> iterator = msg.iterator();
	            while (iterator.hasNext()) {
	            	result.add(iterator.next());}
		        return result;
	    }
		
	
		
		public static void write(String sig, ArrayList<String> listOfString, String jsonPath) {
		int i;
        JSONObject obj = new JSONObject();

        JSONArray list = new JSONArray();
        for (i = 0; i < listOfString.size(); i++) { 
        	list.add(Regex.test(sig, listOfString.get(i)));

            // accessing each element of array 
	}

        obj.put("results", list);

        try (FileWriter file = new FileWriter(jsonPath)) {
            file.write(obj.toJSONString());
        } catch (IOException e) {
            e.printStackTrace();
        }

        System.out.print("Json written in " + jsonPath);

    }
	
}
