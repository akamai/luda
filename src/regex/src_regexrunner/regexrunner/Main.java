package regexrunner;


import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.ParseException;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import regexrunner.JsonOperation;


/**
This code is parsing a list of string, test them agaisnt a regex and 
write the results in a file
* @author  jordang
* @version 1.0
* @since   2020-06-04
*/


public class Main{

    public static void main(String[] args) throws IOException, ParseException {
    	/** args: regex, input json, output json */

    	ArrayList<String> stringList = JsonOperation.read(args[1]);
    	JsonOperation.write(args[0], stringList, args[2]);

    }

}