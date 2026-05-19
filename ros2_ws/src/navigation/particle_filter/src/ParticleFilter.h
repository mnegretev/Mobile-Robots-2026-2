/*
 * MOBILE ROBOTS - UNAM, FI, 2026-2
 * LOCALIZATION BY PARTICLE FILTERS
 *
 * Instructions:
 * Write the code necessary to implement localization by particle filters.
 * Modify only the sections marked with the TODO comment. 
 */
#include "particle_filter/ray_tracer.h"
#define FULL_NAME "Francisco Vera Diaz"

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
	for(int i = 0; i < N; i++)
	{
	    particles[i].x     = rnd.uniformReal(min_x, max_x);
	    particles[i].y     = rnd.uniformReal(min_y, max_y);
	    particles[i].theta = rnd.uniformReal(min_a, max_a);
	}
	/*
	 */
	return particles;
    }

    static void move_particles(std::vector<geometry_msgs::msg::Pose2D>& particles,
			       float delta_x, float delta_y, float delta_t, float sigma2)
    {
	random_numbers::RandomNumberGenerator rnd;
	/*
	 * TODO:
	 * Move each particle a displacement given by delta_x, delta_y and delta_t.
	 * Displacement is given w.r.t. particles's frame, i.e., to calculate the new position for
	 * each particle you need to rotate delta_x and delta_y, on Z axis, an angle theta_i, where theta_i
	 * is the orientation of the i-th particle.
	 * Add gaussian noise to each new position. Use sigma2 as variance.
	 * You can use the function rnd.gaussian(mean, variance)
	 */
	for(size_t i = 0; i < particles.size(); i++)
	{
	    float theta = particles[i].theta;

	    // Rotate the local displacement (delta_x, delta_y) into the world frame
	    // using the particle's current orientation theta_i
	    float world_dx = delta_x * cos(theta) - delta_y * sin(theta);
	    float world_dy = delta_x * sin(theta) + delta_y * cos(theta);

	    // Update position and orientation, adding Gaussian noise
	    particles[i].x     += world_dx + rnd.gaussian(0.0, sigma2);
	    particles[i].y     += world_dy + rnd.gaussian(0.0, sigma2);
	    particles[i].theta += delta_t  + rnd.gaussian(0.0, sigma2);
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

	// For each particle, compute the likelihood using a Gaussian sensor model:
	// p(z | x) = prod_k exp( -(z_k - z_hat_k)^2 / (2 * sigma2) )
	// In log space: log p = sum_k [ -(z_k - z_hat_k)^2 / (2 * sigma2) ]
	// We work in log space for numerical stability, then exponentiate.
	for(size_t i = 0; i < simulated_scans.size(); i++)
	{
	    double log_likelihood = 0.0;

	    size_t num_simulated = simulated_scans[i].ranges.size();

	    for(size_t k = 0; k < num_simulated; k++)
	    {
		// Index into real scan: each simulated ray k corresponds to real ray k*downsampling
		size_t real_idx = k * downsampling;

		if(real_idx >= real_scan.ranges.size())
		    break;

		float sim_range  = simulated_scans[i].ranges[k];
		float real_range = real_scan.ranges[real_idx];

		// Skip invalid (non-finite) readings from either scan
		if(!std::isfinite(sim_range) || !std::isfinite(real_range))
		    continue;

		float diff = real_range - sim_range;
		log_likelihood += -(diff * diff) / (2.0f * sigma2);
	    }

	    // Exponentiate to get likelihood (similarity)
	    similarities[i] = exp(log_likelihood);
	}

	// Normalize so all similarities sum to 1.0 (making them a proper probability distribution)
	double total = 0.0;
	for(size_t i = 0; i < similarities.size(); i++)
	    total += similarities[i];

	// Avoid division by zero: if all similarities are zero, assign uniform weights
	if(total <= 0.0)
	{
	    double uniform = 1.0 / (double)similarities.size();
	    for(size_t i = 0; i < similarities.size(); i++)
		similarities[i] = uniform;
	}
	else
	{
	    for(size_t i = 0; i < similarities.size(); i++)
		similarities[i] /= total;
	}
	
	return similarities;
    }
    
    static int random_choice(std::vector<double>& probabilities)
    {
	random_numbers::RandomNumberGenerator rnd;
	/*
	 * TODO:
	 *
	 * Write an algorithm to choice an integer in the range [0, N-1], with N, the length of 'probabilities'.
	 * Probability of picking an integer 'i' is given by the corresponding probabilities[i] value.
	 * Return the chosen integer. 
	 */

	// Draw a uniform random number in [0, 1)
	double r = rnd.uniformReal(0.0, 1.0);

	// Walk along the cumulative distribution until we exceed r
	// This implements inverse CDF (roulette wheel) sampling
	double cumulative = 0.0;
	for(size_t i = 0; i < probabilities.size(); i++)
	{
	    cumulative += probabilities[i];
	    if(r <= cumulative)
		return (int)i;
	}

	// Fallback: return last index (handles floating point rounding edge cases)
	return (int)probabilities.size() - 1;
    }

    static std::vector<geometry_msgs::msg::Pose2D> resample_particles(
	std::vector<geometry_msgs::msg::Pose2D>& particles, std::vector<double>& probabilities, float sigma2)
    {

	random_numbers::RandomNumberGenerator rnd;
	std::vector<geometry_msgs::msg::Pose2D> resampled_particles(particles.size());
	/*
	 * TODO:
	 * Sample, with replacement, N particles from the set 'particles'.
	 * The probability of the i-th particle to be resampled is given by probabilities[i].
	 * Use the random_choice function to pick a particle with the correct probability.
	 * Add gaussian noise to each sampled particle (add noise to x,y and theta). Use sigma2 as noise variance.
	 */
	for(size_t i = 0; i < resampled_particles.size(); i++)
	{
	    // Pick a particle index according to the probability distribution
	    int chosen = random_choice(probabilities);

	    // Copy that particle and add small Gaussian noise to spread the distribution
	    resampled_particles[i].x     = particles[chosen].x     + rnd.gaussian(0.0, sigma2);
	    resampled_particles[i].y     = particles[chosen].y     + rnd.gaussian(0.0, sigma2);
	    resampled_particles[i].theta = particles[chosen].theta + rnd.gaussian(0.0, sigma2);
	}
	/*
	 */
	return resampled_particles;
    }
    
};