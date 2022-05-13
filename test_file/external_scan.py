def custom_scan(
    exposure_time,
    period,
    out_x,
    out_y,
    out_z,
    rs=1,
    out_r=0,
    xanes_flag=False,
    xanes_angle=0,
    note="",
):
    # Ni
    angle_ini = 0
    yield from mv(zps.pi_r, angle_ini)
    print("start taking tomo and xanes of Ni")
    yield from move_zp_ccd(8.35, move_flag=1)
    yield from fly_scan(
        exposure_time,
        relative_rot_angle=180,
        period=period,
        out_x=out_x,
        out_y=out_y,
        out_z=out_z,
        rs=rs,
        parkpos=out_r,
        note=note + "_8.35keV",
    )
    yield from bps.sleep(2)
    yield from move_zp_ccd(8.3, move_flag=1)
    yield from fly_scan(
        exposure_time,
        relative_rot_angle=180,
        period=period,
        out_x=out_x,
        out_y=out_y,
        out_z=out_z,
        rs=rs,
        parkpos=out_r,
        note=note + "8.3keV",
    )
    yield from mv(zps.pi_r, xanes_angle)
    if xanes_flag:
        yield from xanes_scan2(
            eng_list_Ni,
            exposure_time,
            chunk_size=5,
            out_x=out_x,
            out_y=out_y,
            out_z=out_z,
            out_r=out_r,
            note=note + "_xanes",
        )
    yield from mv(zps.pi_r, angle_ini)

