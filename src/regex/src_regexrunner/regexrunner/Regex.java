package regexrunner;

import java.util.ArrayList;
import java.util.regex.*;  


public class Regex {
	

	
	public static boolean test(String sig, String my_string) {	
	Pattern pattern = Pattern.compile(sig);
	Matcher matcher = pattern.matcher(my_string);
	if (matcher.find())
		return true;
	return false;
		
}
}
