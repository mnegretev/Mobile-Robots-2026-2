/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Instructions:
 * Write the code necessary to implement localization by particle filters.
 * Modify only the sections marked with the TODO comment. 
 */
#include "particle_filter/ray_tracer.h"
#define FULL_NAME "Isaac Jaciel Zambrano Miranda"

class ParticleFilter
{
public:
    ParticleFilter(){}

    static std::vector<geometry_msgs::msg::Pose2D> get_initial_distribution(
    int N, float min_x, float max_x, float min_y, float max_y, float min_a, float max_a)
    {
	random_numbers::RandomNumberGenerator rnd;
	std::vector<geometry_msgs::msg::Pose2D> particles(N);
	for(int i = 0; i < N; i++)
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
	for(size_t i = 0; i < particles.size(); i++)
	{
	    float th = particles[i].theta;
	    particles[i].x     += delta_x * cos(th) - delta_y * sin(th) + rnd.gaussian(0, sigma2);
	    particles[i].y     += delta_x * sin(th) + delta_y * cos(th) + rnd.gaussian(0, sigma2);
	    particles[i].theta += delta_t + rnd.gaussian(0, sigma2);
	}
    }

    static std::vector<sensor_msgs::msg::LaserScan> simulate_particle_scans(
	std::vector<geometry_msgs::msg::Pose2D>& particles,
	nav_msgs::msg::OccupancyGrid& map,
	sensor_msgs::msg::LaserScan& sensor_specs)
    {
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
	std::vector<double> similarities(simulated_scans.size());
	for(size_t i = 0; i < simulated_scans.size(); i++)
	{
	    double log_sim = 0.0;
	    for(size_t j = 0; j < simulated_scans[i].ranges.size(); j++)
	    {
		float r_sim  = simulated_scans[i].ranges[j];
		float r_real = real_scan.ranges[j * downsampling];
		if(!std::isfinite(r_sim) || !std::isfinite(r_real))
		    continue;
		float diff = r_sim - r_real;
		log_sim += -(diff * diff) / (2.0 * sigma2);
	    }
	    similarities[i] = exp(log_sim);
	}
	double total = 0.0;
	for(size_t i = 0; i < similarities.size(); i++)
	    total += similarities[i];
	if(total > 0.0)
	    for(size_t i = 0; i < similarities.size(); i++)
		similarities[i] /= total;
	else
	    for(size_t i = 0; i < similarities.size(); i++)
		similarities[i] = 1.0 / similarities.size();
	return similarities;
    }
    
    static int random_choice(std::vector<double>& probabilities)
    {
	random_numbers::RandomNumberGenerator rnd;
	double x = rnd.uniformReal(0.0, 1.0);
	int i = 0;
	while(i < (int)probabilities.size() - 1)
	{
	    x -= probabilities[i];
	    if(x <= 0.0)
		return i;
	    i++;
	}
	return i;
    }

    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
	std::vector<geometry_msgs::msg::Pose2D>& particles, std::vector<double>& probabilities, float sigma2)
    {
	random_numbers::RandomNumberGenerator rnd;
	std::vector<geometry_msgs::msg::Pose2D> resampled_particles(particles.size());
	for(size_t i = 0; i < particles.size(); i++)
	{
	    int idx = random_choice(probabilities);
	    resampled_particles[i].x     = particles[idx].x     + rnd.gaussian(0, sigma2);
	    resampled_particles[i].y     = particles[idx].y     + rnd.gaussian(0, sigma2);
	    resampled_particles[i].theta = particles[idx].theta + rnd.gaussian(0, sigma2);
	}
	return resampled_particles;
    }
    
};
