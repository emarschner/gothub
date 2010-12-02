/* Functions for extracting stats.
 * To run these, start the mongo shell w/ the processed db and this file:
 *   mongo --shell processed mapreduce_jobs.js
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

// TODO: clean up all these functions to remove duplication, and output
// generic stats

var geo_freq = function() {
    m = function() {if (this.lat && this.long) {emit(String([this.lat, this.long]), 1);}};
    res = db.commits.mapReduce(m, reduce_count);
    total_commits = res.counts.input;
    geo_commits = res.counts.emit;
    unique_geo = res.counts.output;
    fraction_with_geo = geo_commits / total_commits;
    geo_sorted = db[res.result].find().sort({"value": -1});
    return geo_sorted;
};

var loc_by_freq = function() {
    m = function() {if (this.location) {emit(this.location, 1);}};
    res = db.commits.mapReduce(m, reduce_count);
    total_commits = res.counts.input;
    loc_commits = res.counts.emit;
    unique_loc = res.counts.output;
    fraction_with_loc = loc_commits / total_commits;
    loc_sorted = db[res.result].find().sort({"value": -1});
    return loc_sorted;
};

var proj_by_commits = function() {
    m = function() {emit(this.project, 1);}
    res = db.commits.mapReduce(m, reduce_count);
    total_commits = res.counts.input;
    unique_projects = res.counts.output;
    projects_sorted = db[res.result].find().sort({"value": -1});
    return projects_sorted;
};

var proj_by_users = function() {
    // Phase 1: emit (project, author) keys and ignore values
    m = function() {emit({project: this.project, author: this.author}, 1);}
    res = db.commits.mapReduce(m, reduce_count);
    // Phase 2: group by project, list of authors
    m2 = function() {emit(this._id.project, 1);}
    res2 = db[res.result].mapReduce(m2, reduce_count);
    total_commits = res.counts.input;
    unique_projects = res2.counts.output;
    projects_sorted = db[res2.result].find().sort({"value": -1});
    return projects_sorted;
};

var unique_sha1s = function() {
    m = function() {emit(this.sha1, 1);};
    res = db.commits.mapReduce(m, reduce_count);
    total_commits = res.counts.input;
    unique_sha1s = res.counts.output;
    dupes = total_commits - unique_sha1s
    unique_sha1s_check = db[res.result].find().count()
};

// Use on raw only:
var unique_raw_sha1s = function() {
    m = function() {emit(this.id, 1);};
    res = db.commits.mapReduce(m, reduce_count);
    total_commits = res.counts.input;
    unique_sha1s = res.counts.output;
    dupes = total_commits - unique_sha1s
    unique_sha1s_check = db[res.result].find().count()
}