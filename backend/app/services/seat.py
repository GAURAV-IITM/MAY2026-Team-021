"""Seat, shift, allocation, transfer, and availability use cases.

TODO: Allocation writes must lock candidate rows and reject overlapping active
allocations for the same seat or student. Both inclusive date ranges and daily
shift intervals, including intervals crossing midnight, must overlap before a
booking conflicts. Transfers close the old allocation and create a linked new
allocation in the same transaction. Occupied, reserved, and blocked-by-shift
are derived availability states; they are never persisted on the seat row.
"""
