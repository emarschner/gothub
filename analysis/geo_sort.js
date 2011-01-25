/* Functions for extracting stats.
 * To run these, start the mongo shell w/ the processed db and this file:
 *   mongo --shell processed geo_sort.js
 * ... then call functions.
 * If you need more specifics, like job completion times, it may be easier
 * to just copy/paste the lines into the mongo shell.
 */

// Generic reduce function for doing counts
var reduce_count = function(k, vals) {
     var sum=0;
     for(var i in vals) sum += vals[i];
     return sum;
};

var geo_freq = function() {
    m = function() {if (this.lat && this.long) {emit(String([this.lat, this.long]), 1);}};
    res = db.users.mapReduce(m, reduce_count);
    total_users = res.counts.input;
    geo_total = res.counts.emit;
    unique_geo = res.counts.output;
    fraction_with_geo = geo_total / total_users;
    geo_sorted = db[res.result].find().sort({"value": -1});
    return geo_sorted;
};

var loc_by_freq = function() {
    m = function() {if (this.location) {emit(this.location, 1);}};
    res = db.users.mapReduce(m, reduce_count);
    total_users = res.counts.input;
    loc_users = res.counts.emit;
    unique_loc = res.counts.output;
    fraction_with_loc = loc_users / total_users;
    loc_sorted = db[res.result].find().sort({"value": -1});
    return loc_sorted;
};