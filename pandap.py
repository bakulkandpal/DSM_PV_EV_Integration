import pandapower as pp

# Create an empty network
net = pp.create_empty_network()

# Create buses
bus1 = pp.create_bus(net, vn_kv=20, name="Bus 1")
bus2 = pp.create_bus(net, vn_kv=20, name="Bus 2")
bus3 = pp.create_bus(net, vn_kv=20, name="Bus 3")

# Create bus elements
pp.create_ext_grid(net, bus1, vm_pu=1.02, name="Grid Connection")

# Create lines
line1 = pp.create_line_from_parameters(net, from_bus=bus1, to_bus=bus2, length_km=0.5, 
                                       r_ohm_per_km=0.5, x_ohm_per_km=0.5, c_nf_per_km=10, 
                                       max_i_ka=0.2, name="Line 1-2")
line2 = pp.create_line_from_parameters(net, from_bus=bus2, to_bus=bus3, length_km=0.5, 
                                       r_ohm_per_km=0.5, x_ohm_per_km=0.5, c_nf_per_km=10, 
                                       max_i_ka=0.2, name="Line 2-3")

# Create loads
pp.create_load(net, bus2, p_mw=0.1, q_mvar=0.05, name="Load at Bus 2")
pp.create_load(net, bus3, p_mw=0.1, q_mvar=0.05, name="Load at Bus 3")

# Run load flow
pp.runpp(net)

# Print results
print(net.res_bus)
print(net.res_line)


