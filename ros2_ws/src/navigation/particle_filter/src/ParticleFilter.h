/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Instructions:
 * Write the code necessary to implement localization by particle filters.
 * Modify only the sections marked with the TODO comment. 
 */
#include <vector>
#include <cmath>
#include <numeric>
#include "particle_filter/ray_tracer.h"
#define FULL_NAME "Galicia Rioja Angel Daniel "

class ParticleFilter
{
public:
    ParticleFilter(){}

    static std::vector<geometry_msgs::msg::Pose2D> get_initial_distribution(
    int N, float min_x, float max_x, float min_y, float max_y, float min_a, float max_a)
    {
	random_numbers::RandomNumberGenerator rnd;
	std::vector<geometry_msgs::msg::Pose2D> particles(N);
	/*
	 * TODO:
	 * Generate a set of N particles (each particle represented by a Pose2D message)
	 * with positions uniformly distributed within bounding box given by min_x, ..., max_a.
	 * To generate uniformly distributed random numbers, you can use the funcion rnd.uniformReal(min, max)
	 */
	for(int i = 0; i < N; ++i)
	{
	    particles[i].x     = rnd.uniformReal(min_x, max_x);
	    particles[i].y     = rnd.uniformReal(min_y, max_y);
	    particles[i].theta = rnd.uniformReal(min_a, max_a);
	}
	return particles;
    }

    static void move_particles(std::vector<geometry_msgs::msg::Pose2D>& particles,
			       float delta_x, float delta_y, float delta_t, float sigma2)
    {
	random_numbers::RandomNumberGenerator rnd;
	for(size_t i = 0; i < particles.size(); ++i)
	{
	    float theta = particles[i].theta;
	    float cos_t = cos(theta);
	    float sin_t = sin(theta);
	    float world_dx = delta_x * cos_t - delta_y * sin_t;
	    float world_dy = delta_x * sin_t + delta_y * cos_t;

	    float noise_x = rnd.gaussian(0.0f, sigma2);
	    float noise_y = rnd.gaussian(0.0f, sigma2);
	    float noise_theta = rnd.gaussian(0.0f, sigma2);

	    particles[i].x     += world_dx + noise_x;
	    particles[i].y     += world_dy + noise_y;
	    particles[i].theta += delta_t + noise_theta;
	}
    }

    static std::vector<sensor_msgs::msg::LaserScan> simulate_particle_scans(
	std::vector<geometry_msgs::msg::Pose2D>& particles,
	nav_msgs::msg::OccupancyGrid& map,
	sensor_msgs::msg::LaserScan& sensor_specs)
    {
	/*
	 * TODO:
	 * Review the code to simulate a laser scan for each particle given the set of particles and a static map. 
	 */
	std::vector<sensor_msgs::msg::LaserScan> simulated_scans(particles.size());
	for(size_t i=0; i < particles.size(); i++)
	{
	    geometry_msgs::msg::Pose sensor_pose;
	    sensor_pose.position.x    = particles[i].x;
	    sensor_pose.position.y    = particles[i].y;
	    sensor_pose.orientation.w = cos(particles[i].theta/2);
	    sensor_pose.orientation.z = sin(particles[i].theta/2);
	    
	    simulated_scans[i] = ray_tracer::simulateRangeScan(map, sensor_pose, sensor_specs);
	    
	}
	return simulated_scans;
    }

    static std::vector<double> get_particle_similarities(
	std::vector<sensor_msgs::msg::LaserScan>& simulated_scans,
	sensor_msgs::msg::LaserScan& real_scan,
	int downsampling, float sigma2)
    {
	std::vector<double> similarities;
	similarities.resize(simulated_scans.size());
	/*
	 * TODO:
	 * For each particle, calculate the similarity between its simulated scan and the real scan.
	 * Normalize all similarities (the sum of all values must always be 1.0)
	 * Store results in 'similarities'.
	 * IMPORTANT NOTE 1. The real sensor scans are DOWNSAMPLED. That is, only 1 out of 'downsampling' scans is considered, i.e.,
	 * For example, if downsampling=10, then, if real sensor has 500 ranges, simulated scans will only have 50 ranges
	 * When comparing readings, for each reading in the simulated scan, you should skip 'downsampling' readings
	 * in the real sensor.
	 * IMPORTANT NOTE 2. Both, simulated an real scans, can have infinite distances. Thus, when comparing readings,
	 * ensure both simulated and real ranges are finite values. 
	 */
	for(size_t i = 0; i < simulated_scans.size(); ++i)
	{
	    const auto& sim_scan = simulated_scans[i];
	    double error = 0.0;
	    int valid_count = 0;

	    for(size_t j = 0; j < sim_scan.ranges.size(); ++j)
	    {
		int real_index = static_cast<int>(j) * downsampling;
		if(real_index >= static_cast<int>(real_scan.ranges.size()))
		    break;

		float sim_range = sim_scan.ranges[j];
		float real_range = real_scan.ranges[real_index];
		if(std::isfinite(sim_range) && std::isfinite(real_range))
		{
		    double diff = static_cast<double>(sim_range) - static_cast<double>(real_range);
		    error += diff * diff;
		    valid_count++;
		}
	    }

	    if(valid_count > 0)
	    {
		// Use an exponential similarity measure based on squared error.
		double s2 = static_cast<double>(sigma2);
		if(s2 <= 0.0)
		    s2 = 1e-6;
		similarities[i] = exp(-error / (2.0 * s2));
	    }
	    else
	    {
		similarities[i] = 0.0;
	    }
	}

	double total = std::accumulate(similarities.begin(), similarities.end(), 0.0);
	if(total > 0.0)
	{
	    for(double& s : similarities)
		 s /= total;
	}
	else if(!similarities.empty())
	{
	    double uniform_prob = 1.0 / static_cast<double>(similarities.size());
	    for(double& s : similarities)
		 s = uniform_prob;
	}

	return similarities;
    }
    
    static int random_choice(std::vector<double>& probabilities)
    {
	random_numbers::RandomNumberGenerator rnd;
	// Normalize probabilities in case they are not exactly normalized.
	double total = std::accumulate(probabilities.begin(), probabilities.end(), 0.0);
	if(total <= 0.0)
	{
	    if(probabilities.empty())
		return -1;
	    int n = static_cast<int>(probabilities.size());
	    double r = rnd.uniformReal(0.0, 1.0);
	    int index = static_cast<int>(std::floor(r * n));
	    if(index < 0)
		index = 0;
	    else if(index >= n)
		index = n - 1;
	    return index;
	}

	double threshold = rnd.uniformReal(0.0, 1.0) * total;
	double cumulative = 0.0;
	for(int i = 0; i < static_cast<int>(probabilities.size()); ++i)
	{
	    cumulative += probabilities[i];
	    if(cumulative >= threshold)
		return i;
	}

	return static_cast<int>(probabilities.size()) - 1;
    }

    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
	std::vector<geometry_msgs::msg::Pose2D>& particles, std::vector<double>& probabilities, float sigma2)
    {

	random_numbers::RandomNumberGenerator rnd;
	std::vector<geometry_msgs::msg::Pose2D> resampled_particles(particles.size());
	for(size_t i = 0; i < particles.size(); ++i)
	{
	    int index = random_choice(probabilities);
	    if(index < 0 || index >= static_cast<int>(particles.size()))
	    {
		index = 0;
	    }

	    resampled_particles[i] = particles[index];
	    resampled_particles[i].x     += rnd.gaussian(0.0f, sigma2);
	    resampled_particles[i].y     += rnd.gaussian(0.0f, sigma2);
	    resampled_particles[i].theta += rnd.gaussian(0.0f, sigma2);
	}

	return resampled_particles;
    }
    
};
